# To support layered ipk generation

# See release note for configuration details.
RDK_ARTIFACTS_BASE_URL ?= ""

DISTRO = "rdk"

MIDDLEWARE_EXTENSION = "-middleware"

# Middleware IPK configuration

RELEASE_NUM = "8.7.2.0"
MIDDLEWARE_ARCH = "${MACHINE}${MIDDLEWARE_EXTENSION}"
PACKAGE_EXTRA_ARCHS:append = " ${MIDDLEWARE_ARCH}"
OPKG_ARCH_PRIORITY:${MIDDLEWARE_ARCH} = "205"

MW_IPK_PATH ?= "${MIDDLEWARE_ARCH}/${MIDDLEWARE_LAYER_VERSION}/ipks/${BUILD_VARIANT}"
MW_IPK_SERVER_PATH ?= "${RDK_ARTIFACTS_BASE_URL}/${MW_IPK_PATH}"

IPK_FEED_URIS += " \
                ${MIDDLEWARE_ARCH}##${MW_IPK_SERVER_PATH} "

CVE_LAYER_FEED_PATH += "${MIDDLEWARE_ARCH}##file:///home/jenkins/community_shared/raspberrypi4-64-rdke-middleware/tarballs/raspberrypi4-64-rdke-middleware.tgz;sha256sum=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

# Middleware OSS IPK configuration

OSS_LAYER_VERSION = "4.14.0"
MIDDLEWARE_OSS = "${@get_oss_arch(d)}${MIDDLEWARE_EXTENSION}"
PACKAGE_EXTRA_ARCHS:append = "${@ '' if '${MIDDLEWARE_OSS}' == '${OSS_LAYER_ARCH}' else ' ${MIDDLEWARE_OSS}'}"
OPKG_ARCH_PRIORITY:${MIDDLEWARE_OSS} = "210"

MW_OSS_IPK_PATH ?= "${MIDDLEWARE_OSS}/${OSS_LAYER_VERSION}/ipks/"
MW_OSS_IPK_SERVER_PATH ?= "${RDK_ARTIFACTS_BASE_URL}/${MW_OSS_IPK_PATH}"

IPK_FEED_URIS += " \
                ${MIDDLEWARE_OSS}##${MW_OSS_IPK_SERVER_PATH} "

CVE_LAYER_FEED_PATH += "${MIDDLEWARE_OSS}##file:///home/jenkins/community_shared/raspberrypi4-64-rdke-middleware/tarballs/rdk-arm64-oss-middleware.tgz;sha256sum=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
