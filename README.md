
# RDKE Middleware Layer 2.16.0 Release Note

| Summary       | Content |
|---------------|---------|
| Manifest URL  | https://github.com/rdkcentral/middleware-manifest-rdke |
| Release Tag   | [2.16.0](https://github.com/rdkcentral/middleware-manifest-rdke/releases/tag/2.16.0) |
| Yocto Version | Kirkstone |
| Date          | 2025-07-24 17:21:50 UTC |
| Author        | support@rdkcentral.com |


### Middleware Release Details
[Middleware Release 2.16.0](https://github.com/rdkcentral/middleware-manifest-rdke/releases/tag/2.16.0) has the below enlisted layer combination.

| Layer Name | Current Revision/Tag |
|------------|-------------------|
| meta-product-raspberrypi | [4.0.10](https://github.com/rdkcentral/meta-product-raspberrypi/tree/4.0.10) |
| meta-vendor-raspberrypi-release | [4.5.1](https://github.com/rdkcentral/meta-vendor-raspberrypi-release/tree/4.5.1) |
| build-scripts | [1.0.1](https://github.com/rdkcentral/build-scripts/tree/1.0.1) |
| meta-stack-layering-support | [2.0.1](https://github.com/rdkcentral/meta-stack-layering-support/tree/2.0.1) |
| meta-rdk-auxiliary | [1.3.0](https://github.com/rdkcentral/meta-rdk-auxiliary/tree/1.3.0) |
| rdke-common-config | [1.0.4](https://github.com/rdkcentral/rdke-common-config/tree/1.0.4) |
| rdke-stb-config | [1.0.0](https://github.com/rdkcentral/rdke-stb-config/tree/1.0.0) |
| meta-oss-reference-release | [4.6.2-community](https://github.com/rdkcentral/meta-oss-reference-release/tree/4.6.2-community) |
| meta-rdk-oss-reference | [1.2.0](https://github.com/rdkcentral/meta-rdk-oss-reference/tree/1.2.0) |
| meta-oss-common-config | [1.1.0](https://github.com/rdkcentral/meta-oss-common-config/tree/1.1.0) |
| meta-openembedded | [rdk-4.0.0](https://github.com/rdkcentral/meta-openembedded/tree/rdk-4.0.0) |
| poky | [rdk-4.2.1](https://github.com/rdkcentral/poky/tree/rdk-4.2.1) |
| meta-python2 | [rdk-4.0.0](https://github.com/rdkcentral/meta-python2/tree/rdk-4.0.0) |
| meta-rdk-halif-headers | [3.0.0](https://github.com/rdkcentral/meta-rdk-halif-headers/tree/3.0.0) |
| meta-middleware-generic-support | [1.8.0](https://github.com/rdkcentral/meta-middleware-generic-support/tree/1.8.0) |
| meta-rdk | [1.8.0](https://github.com/rdkcentral/meta-rdk/tree/1.8.0) |
| meta-rdk-video | [1.8.0](https://github.com/rdkcentral/meta-rdk-video/tree/1.8.0) |

For a comprehensive list of changes, updates, and release history, refer to the [Changelog](CHANGELOG.md).

The [packages and versions](MiddlewarePackagesAndVersions.md) file provides the list of packages in this Middleware release.

List of features: Upcoming

Test Report: [Upcoming test report url](Upcoming test report url)

For RDKE Middleware layer specific build instructions, refer [this](https://github.com/rdkcentral/middleware-manifest-rdke/blob/2.16.0/README.md)

## License Details
This project is distributed under the terms outlined in the associated [License](LICENSE) and [Notice](NOTICE) files. Please review these files for detailed information.

---

#### How to update this README automatically

1. Generate `PackagesAndVersions.md` for the target `PACKAGE_ARCH` by building the Middleware stack for `2.16.0` with `DEPLOY_IPK_FEED = "1"` and `GENERATE_IPK_VERSION_DOC = "1"` in `${BUILDDIR}/conf/local.conf`. The generated file will be in `${BUILDDIR}/tmp/deploy/ipk/${PACKAGE_ARCH}/` and replace here as `MiddlewarePackagesAndVersions.md`. See [variables.md](https://github.com/rdkcentral/meta-stack-layering-support/blob/2.0.1/docs/variables.md) for supported options.
2. Run `Tools/update_readme.py` script from base directory to generate the final README. Note: change to match Host's shell conventions and filesystem path syntax(Windows/Linux/Mac).
```sh
# Requires Python 3.x
# Setup requirements (one time): pip install requests
# RDKE_LAYER can be Vendor/Middleware/Application
Usage: python3 ./Tools/update_readme.py ./Tools/README_TEMPLATE.md ./README.md <MANIFEST_REPO_BASE_URL> <MANIFEST_NAME> 2.16.0 Middleware "AUTHOR,email" "TestReportUrl"
```
- Replace the arguments with the actual release/tag/commit values matching the release.

Eg (Linux Host):
```sh
python3 ./Tools/update_readme.py ./Tools/README_TEMPLATE.md ./README.md https://github.com/rdkcentral/vendor-manifest-raspberrypi rdke-raspberrypi.xml 4.5.1 Middleware "ReleaseTeam, email_id" "https://example.com/test-report"
```

---
