"""toil_cnvkit commands tests."""

from os import environ
from os.path import join
from os.path import abspath
from os.path import dirname

import pytest
import click

from toil_cnvkit import __version__
from toil_cnvkit import commands
from toil_cnvkit import validators

ROOT = abspath(dirname(__file__))


@pytest.fixture
def input_params():
    return {
        'tumor_file': join(ROOT, 'data', 'tumor', 'tumor.bam'),
        'normal1_file': join(ROOT, 'data', 'normals', 'normal1.bam'),
        'normal2_file': join(ROOT, 'data', 'normals', 'normal2.bam'),
        'fasta_file': join(ROOT, 'data', 'references', 'reference.fasta'),
        'access_file': join(ROOT, 'data', 'references', 'reference.access.bed'),
        'bed_file': join(ROOT, 'data', 'references', 'targets.bed'),
        'ref_file': join(ROOT, 'data', 'references', 'reference.cnn'),
    }


def assert_expected_output_files(outdir, check_reference=True):
    """Make sure expected output files exist and are not empty."""

    tumor_name = 'tumor'
    expected_files = [
        # Output files of CNVKIT Analysis
        join(outdir, tumor_name + ".cns"),
        join(outdir, tumor_name + ".interval_count"),
        join(outdir, tumor_name + "-diagram.pdf"),
        join(outdir, tumor_name + "-diagram.png"),
        join(outdir, tumor_name + "-scatter.pdf"),
        join(outdir, tumor_name + "-scatter.png"),

        # Output files of THetA2 Analysis
        join(outdir, tumor_name + ".n2.withBounds"),
        join(outdir, tumor_name + ".n2.results"),
        join(outdir, tumor_name + ".n2.graph.pdf"),
        join(outdir, tumor_name + ".n2.graph.png"),
        join(outdir, tumor_name + "_caveman_tumour_cn_input.txt"),
        join(outdir, tumor_name + "_caveman_normal_cn_input.txt"),
        join(outdir, "CAVEMAN_NCONTAMINATION.txt"),
        ]

    if check_reference:
        expected_files.append(join(outdir, "reference.cnn"))

    assert validators.validate_patterns_are_files(
        expected_files,
        check_size=True,
        )


def test_new_reference_one_normal(tmpdir, input_params):
    """Sample test for the main command.
    Creaty a new copy number reference.
    """
    outdir = str(tmpdir)
    jobstore = join(str(tmpdir), "jobstore")

    # Build command.
    args = [
        jobstore,
        "--run-theta",
        "--tumor", input_params['tumor_file'],
        "--normal", input_params['normal1_file'],
        "--access", input_params['access_file'],
        "--fasta", input_params['fasta_file'],
        "--bedfile", input_params['bed_file'],
        "--outdir", outdir,
        ]

    # Get and validate options.
    parser = commands.get_parser()
    options = parser.parse_args(args)
    options = commands.process_parsed_options(options)

    # Call pipeline
    commands.run_toil(options)

    # Output files.
    assert_expected_output_files(outdir, check_reference=True)


def test_new_ref_multiple_normals(tmpdir, input_params):
    """Sample test for the main command.
    Creaty a new copy number reference.
    """
    outdir = str(tmpdir)
    jobstore = join(str(tmpdir), "jobstore")

    # Build command.
    args = [
        jobstore,
        "--run-theta",
        "--tumor", input_params['tumor_file'],
        "--normal", input_params['normal1_file'], input_params['normal2_file'],
        "--access", input_params['access_file'],
        "--fasta", input_params['fasta_file'],
        "--bedfile", input_params['bed_file'],
        "--outdir", outdir,
        ]

    # Get and validate options.
    parser = commands.get_parser()
    options = parser.parse_args(args)
    options = commands.process_parsed_options(options)

    # Call pipeline
    commands.run_toil(options)

    # Output files.
    assert_expected_output_files(outdir, check_reference=True)


def test_existing_reference(tmpdir, input_params):
    """Sample test for the main command.
    Using an existing copy number reference.
    """
    outdir = str(tmpdir)
    jobstore = join(str(tmpdir), "jobstore")

    # Build command.
    args = [
        jobstore,
        "--run-theta",
        "--tumor", input_params['tumor_file'],
        "--reference", input_params['ref_file'],
        "--outdir", outdir,
        ]

    # Get and validate options.
    parser = commands.get_parser()
    options = parser.parse_args(args)
    options = commands.process_parsed_options(options)

    # Call pipeline
    commands.run_toil(options)

    # Output files.
    assert_expected_output_files(outdir, check_reference=False)


def test_bad_commands(tmpdir, input_params):
    """Sample test for the main command.
    Creaty a new copy number reference.
    """
    outdir = str(tmpdir)
    jobstore = join(str(tmpdir), "jobstore")

    # Build command args without normal.
    args_no_normal = [
        jobstore,
        "--run-theta",
        "--tumor", input_params['tumor_file'],
        "--outdir", outdir,
        ]

    # Build command args with normal but missing files.
    args_normal_incomplete = [
        jobstore,
        "--run-theta",
        "--tumor", input_params['tumor_file'],
        "--normal", input_params['normal1_file'],
        "--outdir", outdir,
        ]

    # Build command args with normal and reference.
    args_normal_ref = [
        jobstore,
        "--run-theta",
        "--tumor", input_params['tumor_file'],
        "--normal", input_params['normal1_file'],
        "--reference", input_params['ref_file'],
        "--outdir", outdir,
        ]

    parser = commands.get_parser()

    # Check that command without --normal raises error.
    # System Exit prints the error in system stdout
    with pytest.raises(click.UsageError) as exec_info:
        options = parser.parse_args(args_no_normal)
        options = commands.process_parsed_options(options)
        commands.run_toil(options)

    expected_error_message = "argument --normal is required"
    assert expected_error_message in exec_info.value

    # Check that command with incomplete args for
    # new reference raises error.
    with pytest.raises(click.UsageError) as exec_info:
        options = parser.parse_args(args_normal_incomplete)
        options = commands.process_parsed_options(options)
        commands.run_toil(options)

    expected_error_message = (
        "normal, bedfile, access and fasta are required "
        "if '--reference' is not provided."
        )
    assert expected_error_message in exec_info.value

    # Check that command with --normal and --reference
    # args raises error.
    with pytest.raises(click.UsageError) as exec_info:
        options = parser.parse_args(args_normal_ref)
        options = commands.process_parsed_options(options)
        commands.run_toil(options)

    expected_error_message = (
        "Only tumor bam required when using "
        "'--reference'."
        )
    assert expected_error_message in exec_info.value
