REQUIREMENTS = "requirements.txt"


def learn_requirements():
    """
    list all installation requirements

    ALL packages & version restrictions stated in requirements.txt
    """
    import os

    path = os.path.dirname(__file__)
    req_file = os.path.join(path, "..", "..", REQUIREMENTS)
    reqs = []
    if not os.path.exists(req_file):
        # not needed with installed package
        return reqs

    excludes = "versioneer coveralls coverage".split()
    with open(req_file, "r") as fp:
        buf = fp.read().strip().splitlines()
        for req in buf:
            req = req.strip()
            if (
                req != ""
                and not req.startswith("#")
                and req not in excludes
            ):
                reqs.append(req)
    return reqs

# -----------------------------------------------------------------------------
# :author:    Pete R. Jemian
# :email:     prjemian@gmail.com
# :copyright: (c) 2014-2022, Pete R. Jemian
#
# Distributed under the terms of the Creative Commons Attribution 4.0 International Public License.
#
# The full license is in the file LICENSE.txt, distributed with this software.
# -----------------------------------------------------------------------------
