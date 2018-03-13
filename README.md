# toil_cnvkit

[![pypi badge][pypi_badge]][pypi_base]
[![travis badge][travis_badge]][travis_base]
[![codecov badge][codecov_badge]][codecov_base]
[![docker badge][docker_badge]][docker_base]
[![docker badge][automated_badge]][docker_base]

🍋 CNVkit implementation with Toil.

## Features

* 📦 &nbsp; **Easy Installation**

        pip install toil_cnvkit

* 🍉 &nbsp; **Usage Documentation**

        toil_cnvkit --help

* 🐳 &nbsp; **Containers Support**

        toil_cnvkit
            --volumes <local path> <container path>
            --docker {or --singularity} <image path or name>
            jobstore
        

## Contributing

Contributions are welcome, and they are greatly appreciated, check our [contributing guidelines](.github/CONTRIBUTING.md)!

## Credits

This package was created using [Cookiecutter] and the
[leukgen/cookiecutter-toil] project template.

<!-- References -->
[singularity]: http://singularity.lbl.gov/
[docker2singularity]: https://github.com/singularityware/docker2singularity
[cookiecutter]: https://github.com/audreyr/cookiecutter
[leukgen/cookiecutter-toil]: https://github.com/leukgen/cookiecutter-toil

<!-- Badges -->
[docker_base]: https://hub.docker.com/r/leukgen/toil_cnvkit
[docker_badge]: https://img.shields.io/docker/build/leukgen/toil_cnvkit.svg
[automated_badge]: https://img.shields.io/docker/automated/leukgen/toil_cnvkit.svg
[codecov_badge]: https://codecov.io/gh/leukgen/toil_cnvkit/branch/master/graph/badge.svg
[codecov_base]: https://codecov.io/gh/leukgen/toil_cnvkit
[pypi_badge]: https://img.shields.io/pypi/v/toil_cnvkit.svg
[pypi_base]: https://pypi.python.org/pypi/toil_cnvkit
[travis_badge]: https://img.shields.io/travis/leukgen/toil_cnvkit.svg
[travis_base]: https://travis-ci.org/leukgen/toil_cnvkit
