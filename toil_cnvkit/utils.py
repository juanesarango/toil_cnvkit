"""toil_cnvkit utils."""

import os
import tarfile

from pysam import AlignmentFile

from toil_cnvkit import exceptions


def force_link(src, dst):
    """Force a link between src and dst."""
    try:
        os.unlink(dst)
        os.link(src, dst)
    except OSError:
        os.link(src, dst)


def force_symlink(src, dst):
    """Force a symlink between src and dst."""
    try:
        os.unlink(dst)
        os.symlink(src, dst)
    except OSError:
        os.symlink(src, dst)


def tar_dir(output_path, source_dir):
    """Compress a `source_dir` in `output_path`."""
    with tarfile.open(output_path, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))


def get_sample_name(bamfile):
    """Find SM tags for bamfile."""
    tumor_pysam = AlignmentFile(bamfile, "rb")
    tumor_name = ""

    # Get Sample name from bamfile.
    for key in ["RG", "SQ"]:

        # Don't loop through SQ if SM tags are found in RG.
        if tumor_name: break

        for i in tumor_pysam.header[key]:
            if "SM" in i:
                tumor_name = i["SM"]
                break

    if not tumor_name:
        raise exceptions.ConfigurationError(
            "SM tag is missing in tumor bamfile, "
            "could not determine sample name."
            )

    return tumor_name
