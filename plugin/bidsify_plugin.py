import os
import json

from glob import glob

from bidsme.bidsMeta import BidsSession
from bidsme.plugins.tools.General import CheckSeries

# Will integrate plugin into logging
import logging
logger = logging.getLogger(__name__)

base_path = os.path.dirname(__file__)
base_path = os.path.dirname(base_path)

# global variables
preparefolder = ""
bidsfolder = ""
dry_run = False

# Participants lists
white_list = {}
black_list = {}


def InitEP(source: str, destination: str,
           dry: bool,
           **kwargs) -> int:
    global preparefolder
    global bidsfolder
    global dry_run
    preparefolder = source
    bidsfolder = destination
    dry_run = dry

    # Getting white, black and ignore lists
    global white_list
    global black_list
    global remove_list
    lists_path = os.path.join(base_path, "lists")

    white_list = load_white_list(lists_path, "white_list")
    black_list = load_white_list(lists_path, "black_list", modalities=False)


def SubjectEP(scan: BidsSession) -> int:
    if scan.subject in black_list and not black_list[scan.subject]:
        logger.info("Subject {} in black list".format(scan.subject))
        return -1


def SessionEP(session: BidsSession) -> int:
    if session.subject in black_list:
        if session.session or session.session in black_list[session.subject]:
            logger.info("Session {} in black list".format(session.session))
            return -1

    # Checking acquisition list
    if not check_prepared(preparefolder, session, white_list):
        return -1


def SequenceEP(recording):
    
    # Setting up custom variable
    # Applicable only for MRI
    if recording.Module() == "MRI":
        recording.custom["dummies"] = \
                recording.getAttribute("AcquisitionNumber") - 1


# Helper functions
def load_white_list(pth, suffix, modalities=True):
    """
    Search for list json file in provided path, and parcing
    contained lists.
    """
    res = {}

    if modalities:
        suffix = "_{}.json".format(suffix)

        for l_pth in glob(os.path.join(pth, "*" + suffix)):
            fname = os.path.basename(l_pth)
            mod = fname[:-len(suffix)]
            logger.info("Loading {}".format(l_pth))
            with open(l_pth) as f:
                res[mod] = json.load(f)
    else:
        l_pth = os.path.join(pth, suffix + ".json")
        if os.path.isfile(l_pth):
            logger.info("Loading {}".format(l_pth))
            with open(l_pth) as f:
                res = json.load(f)

    return res


def check_prepared(bidsfolder, session, white_list):
    """
    Compares prepared list of acquisitions with list
    from white list, produce error if discrepency is
    found
    """
    sub = session.subject
    ses = session.session if session.session else "ses-"

    for mod in white_list:
        path = os.path.join(bidsfolder, session.getPath(True), mod)

        default = white_list[mod].get("default", {})
        check_list = white_list[mod].get(sub, {})

        acqs = []
        if isinstance(check_list, dict):
            acqs = check_list.get(ses, [])
        elif ses != "ses-":
            logger.warning("Can't interpret {} as sequences to check"
                           .format(check_list))

        if acqs:
            logger.info("{}/{}: Comparing acquisitions with white list"
                        .format(sub, ses))
        else:
            if isinstance(default, dict):
                acqs = default.get(ses, [])
            elif ses != "ses-":
                logger.warning("Can't interpret {} as sequences to check"
                               .format(default))
        if acqs:
            logger.info("{}/{}: Comparing acquisitions with default list"
                        .format(sub, ses))
            if not CheckSeries(path, acqs, strict=True):
                logger.error("{}/{} Series do not match expectation."
                             .format(sub, ses))
                return False
    return True
