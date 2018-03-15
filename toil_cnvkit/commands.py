"""toil_cnvkit commands."""

from glob import glob
from os.path import join
import os
import subprocess

import click
from toil.common import Toil
from toil_container import ContainerArgumentParser
from toil_container import ContainerJob
import pandas as pd

from toil_cnvkit import __version__
from toil_cnvkit import utils


class CNVkit(ContainerJob):

    """Class used to run the CNVkit job."""

    def run(self, fileStore):
        """
        Run CNVkit.

        This function executes cnvkit in two possible ways; either using an
        existing copy number reference

            cnvkit.py batch {tumor-file}
                --diagram
                --scatter
                --output-dir {output-dir}
                --reference {ref-file}

        Or by creating a new copy number reference:

            cnvkit.py batch {tumor-file}
                --diagram
                --scatter
                --output-dir {output-dir}
                --normal {1} {2} {3}... --normal {N}
                --targets {bed-file}
                --fasta {genome-ref-fasta}
                --output-reference {output-ref-file}
                --access {access}
                --processes 1
        """
        # Unset display to run cnvkit regardless X11 settings
        if "DISPLAY" in os.environ:
            del os.environ["DISPLAY"]

        # Use a headless matplotlib backend Agg
        os.environ["MPBACKEND"] = "Agg"

        # Log Options to fileStore
        fileStore.logToMaster(str(self.options))

        # Build the command for CNVkit
        cmd = [
            "cnvkit.py", "batch", self.options.tumor,
            "--output-dir", self.options.outdir,
            "--diagram",
            "--scatter",
        ]

        if self.options.reference:
            cmd += ["--reference", self.options.reference]

        else:
            cmd += [
                "--processes", "1",
                "--targets", self.options.bedfile,
                "--fasta", self.options.fasta,
                "--access", self.options.access,
                "--output-reference", self.options.output_reference,
                "--normal"
            ] + self.options.normal

        output = self.call(cmd, check_output=True)
        fileStore.logToMaster(output)


class FormatCNVkit(ContainerJob):

    """Job to format CNVkit ouptut as valid input for THetA."""

    def run(self, fileStore):
        """Get THetA input `cnvkit.py export theta`."""
        reference = self.options.reference or self.options.output_reference

        tumor_segment = join(
            self.options.outdir,
            self.options.tumor_name + ".cns"
        )
        output = join(
            self.options.outdir,
            self.options.tumor_name + ".interval_count"
        )

        cmd = [
            "cnvkit.py", "export", "theta", tumor_segment,
            "--reference", reference,
            "--output", output
        ]

        output = self.call(cmd, check_output=True)
        fileStore.logToMaster(output)


class Theta(ContainerJob):

    """Job Class to run the THetA - Tumor Heterogeneity Analysis."""

    def run(self, fileStore):
        """
        Run the THetA Analysis.

        RunTHetA --help says:

            MIN_FRAC: The minimum fraction of the genome that must have a
            potential copy number aberration to be a valid sample for THetA
            analysis.

        However, many times you have samples without CN alterations and we
        don't want to fail the pipeline for this reason. As such, We call
        RunTHetA with `MIN_FRAC` set to 0:

            RunTHetA {tumor-file.interval_count}
                --DIR {run-dir}
                --FORCE
                --MIN_FRAC 0
                --N 2
        """
        # Where's the output directory of formatTheta
        interval = join(
            self.options.outdir, self.options.tumor_name + ".interval_count",
        )

        # Build the command
        # Make sure MIN_FRAC is 0 so that plain genomes are run anyways.
        # RunTHeta's default requires 5% of genome with CN aletrations to run.
        cmd = [
            "RunTHetA", interval,
            "--DIR", self.options.outdir,
            "--FORCE",
            "--MIN_FRAC", "0",
            "--N", "2",
        ]

        output = self.call(cmd, check_output=True)
        fileStore.logToMaster(output)


class FormatTheta(ContainerJob):

    """Class Job to format the THetA output for Caveman input."""

    def run(self, fileStore):
        """
        Format theta results for Caveman input.

        Based on this input:

            outdir/{tumor_name}.n2.results
            outdir/{tumor_name}.n2.withBounds

        Write the following files:

            outdir/{tumor_name}._caveman_tumour_cn_input.txt
            outdir/{tumor_name}._caveman_normal_cn_input.txt
        """
        fileStore.logToMaster("Format THetA")
        tumor_name = self.options.tumor_name
        outdir = self.options.outdir

        # Get intervals. See:
        # github.com/raphael-group/THetA/blob/master/doc/MANUAL.txt#L258
        theta_bounds = join(outdir, tumor_name + ".n2.withBounds")
        df = pd.read_csv(theta_bounds, delimiter="\t")
        tcn = df[["chrm", "start", "end"]].copy()
        ncn = tcn.copy()

        # Parse integer copy number prediction, see:
        # https://github.com/raphael-group/THetA/blob/master/doc/MANUAL.txt#L23
        # Found a string integer CN when running using a batch of normals.
        # Thats the reason of `e.isdigit()`, please see the following ticket:
        # https://github.com/raphael-group/THetA/issues/17
        theta_results = join(outdir, tumor_name + ".n2.results")
        results = pd.read_csv(theta_results, delimiter="\t")
        ncn["zint_cpnumber"] = 2
        tcn["zint_cpnumber"] = [
            int(e) if e.isdigit() else 0 for e in results["C"][0].split(":")
        ]

        # Write files.
        toutname = join(outdir, tumor_name + "_caveman_tumour_cn_input.txt")
        noutname = join(outdir, tumor_name + "_caveman_normal_cn_input.txt")
        tcn.to_csv(toutname, sep="\t", index=False, header=False)
        ncn.to_csv(noutname, sep="\t", index=False, header=False)
        fileStore.logToMaster("Wrote %s." % toutname)
        fileStore.logToMaster("Wrote %s." % noutname)

        # Write normal contamination input.
        ncontamination = str(results["mu"][0].split(",")[0])
        ncoutname = join(outdir, "CAVEMAN_NCONTAMINATION.txt")
        with open(ncoutname, "w") as f:
            fileStore.logToMaster("Wrote %s." % ncoutname)
            f.write(ncontamination)


class PDF2PNG(ContainerJob):

    """Class Job to convert PDF results to PNG images."""

    def run(self, fileStore):
        """
        Generate pngs, If the convert command is available.

        Use the `convert` command as follows:

            convert
                -trim
                -flatten
                -density 300
                -quality 100
                -sharpen 0x1.0
                {pdf-file} {ouput-file}
        """
        for pdf_file in glob(join(self.options.outdir, "*.pdf")):
            cmd = [
                "convert",
                "-trim",
                "-flatten",
                "-density", "300",
                "-quality", "100",
                "-sharpen", "0x1.0",
                pdf_file, pdf_file.replace(".pdf", ".png")
            ]

            output = self.call(cmd, check_output=True)
            fileStore.logToMaster(output)


def run_toil(options):
    """Toil implementation for toil_cnvkit."""
    # Define the jobs that always be ran
    cnvkit = CNVkit(
        cores=1,
        memory="10G",
        options=options,
        )

    pdf_to_png = PDF2PNG(
        cores=1,
        memory="10G",
        options=options,
        )

    # if flag --run-theta=true create extra jobs
    if options.run_theta:
        format_cnvkit = FormatCNVkit(
            cores=1,
            memory="10G",
            options=options,
            )

        theta = Theta(
            cores=1,
            memory="10G",
            options=options,
            )

        format_theta = FormatTheta(
            cores=1,
            memory="10G",
            options=options,
            )

        # Build pipeline DAG.
        cnvkit.addChild(format_cnvkit)
        format_cnvkit.addChild(theta)
        theta.addChild(format_theta)

    cnvkit.addFollowOn(pdf_to_png)

    # Execute the pipeline.
    with Toil(options) as pipe:
        if not pipe.options.restart:
            pipe.start(cnvkit)
        else:
            pipe.restart()


def get_parser():
    """Get pipeline options using toil_container ContainerArgumentParser."""
    parser = ContainerArgumentParser(
        version=__version__,
        description="Run toil_cnvkit pipeline."
        )

    # We need to add a group of arguments specific to the pipeline.
    settings = parser.add_argument_group("Cnvkit general options")

    settings.add_argument(
        "--outdir",
        help="Copy number reference file (.cnn).",
        required=True,
        type=click.Path(writable=True, resolve_path=True)
        )

    settings.add_argument(
        "--tumor",
        help="Tumor bam file (.bam).",
        required=True,
        type=click.Path(file_okay=True, readable=True, resolve_path=True)
        )

    settings.add_argument(
        "--run-theta",
        help="Flag to run THetA: the Tumor Heterogeneity Analysis.",
        default=False,
        action="store_true",
        )

    # Add separate section to construct CN reference.
    settings = parser.add_argument_group(
        "To construct a new copy number reference:"
        )

    settings.add_argument(
        "--normal",
        nargs="*",
        help="List of Normal bams to construct the pooled reference (.bam).",
        action="append",
        required=False,
        type=click.Path(file_okay=True, readable=True, resolve_path=True)
        )

    settings.add_argument(
        "--fasta",
        help="Reference genome (.fasta).",
        required=False,
        type=click.Path(file_okay=True, readable=True, resolve_path=True)
        )

    settings.add_argument(
        "--bedfile",
        help="Bam Tumor bed file (.bed).",
        required=False,
        type=click.Path(file_okay=True, readable=True, resolve_path=True)
        )

    settings.add_argument(
        "--access",
        help="Regions of accessible sequence on chromosomes (.bed) "
        "as output by the 'cnvkit.py access' command.",
        required=False,
        type=click.Path(file_okay=True, readable=True, resolve_path=True)
        )

    settings.add_argument(
        "--output-reference",
        help="Output filename/path for the new reference file.",
        required=False,
        type=click.Path(writable=True, resolve_path=True),
        default="reference.cnn",
        )

    # Separate section to use an existing reference.
    settings = parser.add_argument_group("To reuse an existing reference:")

    settings.add_argument(
        "--reference",
        help="Copy number reference file (.cnn).",
        required=False,
        type=click.Path(file_okay=True, readable=True, resolve_path=True)
        )
    return parser


def process_parsed_options(options):
    """Perform validations and add post parsing attributes to `options`."""
    # Make sure the toil logs directory exists.
    if options.writeLogs is not None:
        subprocess.check_call(["mkdir", "-p", options.writeLogs])

    # Flatten list to allow -n 1 2 3 -n 4 -n 5 (using "*" and "append").
    if options.normal:
        options.normal = [i for normals in options.normal for i in normals]

    build_reference_required = [
        options.normal,
        options.bedfile,
        options.access,
        options.fasta,
        ]

    if not options.normal and not options.reference:
        raise click.UsageError(
            "argument --normal is required"
            )
    elif any(build_reference_required) and options.reference:
        raise click.UsageError(
            "Only tumor bam required when using '--reference'."
            )

    elif not all(build_reference_required) and options.normal:
        raise click.UsageError(
            "normal, bedfile, access and fasta are required if "
            "'--reference' is not provided."
            )

    elif all(build_reference_required) and not options.reference:
        options.output_reference = join(
            options.outdir,
            "reference.cnn",
            )

    # Get sample name fron SM bam tag.
    options.tumor_name = utils.get_sample_name(options.tumor)
    return options


def main():
    """
    Parse options and run toil.

    **Workflow**

    1. Define Options `get_parser`: build an `arg_parse` object that
       includes both toil options and pipeline specific options. These will be
       separated in different sections of the `--help` text and used by the
       jobs to do the work.

    2. Validate with `process_parsed_options`: once the options are parsed, it
       maybe necessary to conduct *post-parsing* operations such as adding new
       attributes to the `options` namespace or validating combined arguments.

    3. Execute with `run_toil`: this function uses the `options` namespace to
       build and run the toil `DAG`.
    """
    options = get_parser().parse_args()
    options = process_parsed_options(options=options)
    run_toil(options=options)
