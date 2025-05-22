# To support layered ipk generation

DISTRO = "rdk"

MIDDLEWARE_ARCH = "${MACHINE}-middleware"
PACKAGE_EXTRA_ARCHS:append = " ${MIDDLEWARE_ARCH}"

# See release note for configuration details.
RDK_ARTIFACTS_BASE_URL ?= ""

RELEASE_NUM = "3.2.0"
MW_IPK_PATH = "${MIDDLEWARE_ARCH}/${RELEASE_NUM}/ipks/${BUILD_VARIANT}"
#MW_IPK_SERVER_PATH = "${RDK_ARTIFACTS_BASE_URL}/${MW_IPK_PATH}"
MW_IPK_SERVER_PATH = "https://partners.artifactory.comcast.com/artifactory/rdke-rdkm/raspberrypi4-64-rdke-middleware/dev/RDK7RM-53/ipks/debug/"

IPK_FEED_URIS += " \
                ${MIDDLEWARE_ARCH}##${MW_IPK_SERVER_PATH} "
