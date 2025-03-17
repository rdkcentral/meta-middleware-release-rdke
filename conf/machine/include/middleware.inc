# To support layered ipk generation

DISTRO = "rdk"

MIDDLEWARE_ARCH = "${MACHINE}-middleware"
PACKAGE_EXTRA_ARCHS:append = " ${MIDDLEWARE_ARCH}"

RDK_ARTIFACTS_BASE_URL ??= "https://partners.artifactory.comcast.com/artifactory"
RELEASE_NUM = "2.7.0"

MW_IPK_PATH = "middleware-release/${RELEASE_NUM}/${MACHINE}/ipks"
#MW_IPK_PATH = "middleware-release/${RELEASE_NUM}/${MACHINE}/ipks/${BUILD_VARIANT}"
MW_IPK_SERVER_PATH = "${RDK_ARTIFACTS_BASE_URL}/${MW_IPK_PATH}"

IPK_FEED_URIS += " \ 
                ${MIDDLEWARE_ARCH}##${MW_IPK_SERVER_PATH} "
