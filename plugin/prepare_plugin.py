import os
import shutil
import pandas
import json

from glob import glob

# List of personalized, plugin-related errors
from bidsme.bidsMeta import BidsSession
from bidsme.plugins.tools.General import CheckSeries
from bidsme.plugins.tools.Nibabel import Convert3Dto4D

# Will integrate plugin into logging
import logging
logger = logging.getLogger(__name__)

base_path = os.path.dirname(__file__)
base_path = os.path.dirname(base_path)

# global variables
rawfolder = ""
bidsfolder = ""
dry_run = False

# Participants dataframe
sub_df = None


# Participants lists
white_list = {}
black_list = {}
remove_list = {}

# List of acquisitions to merge into 4D
merge_4D = ["cmrr_mbep2d_bold_mb2_rest",
            "cmrr_mbep2d_bold_mb2_rest_invertpe"]

# List of acquisitions to remove dummy volumes
task_prot = ["cmrr_mbep2d_bold_mb2_rest"]
n_dummies = 4


def InitEP(source: str, destination: str,
           dry: bool,
           **kwargs) -> int:
    global rawfolder
    global bidsfolder
    global dry_run
    rawfolder = source
    bidsfolder = destination
    dry_run = dry

    # Uncomment the next to load participants table
    """
    global sub_df
    # demo_path = os.path.join(rawfolder, "participants.txt")
    demo_path = os.path.join(rawfolder, "FCAVC_demog_bids.xlsx")

    logger.info("Loading demographic data from {}"
                .format(demo_path))
    sub_df = pandas.read_excel(demo_path,
                               index_col="ID")
    # Checking for duplicates
    dupl = sub_df.index.duplicated()
    if dupl.any():
        logger.error("Demographic table has following "
                     "duplicated subjects: {}"
                     .format(sub_df.index[dupl].to_list()))
        return 1
    """

    # Getting white, black and ignore lists
    global white_list
    global black_list
    global remove_list
    lists_path = os.path.join(base_path, "lists")

    white_list = load_white_list(lists_path, "white_list")
    black_list = load_white_list(lists_path, "black_list", modalities=False)
    remove_list = load_white_list(lists_path, "to_remove")
    return 0


def SubjectEP(scan: BidsSession) -> int:

    # Uncomment the following if using demographic table
    """
    if scan.subject not in sub_df.index:
        logger.error("Subject {} not in demographic table"
                     .format(scan.subject))
        return -1

    sub_row = sub_df.loc[scan.subject]
    sub_id = int(scan.subject.rsplit("_")[1])

    # This will rename current subject
    scan.subject = "sub-{}{:03d}".format(sub_row["Group"], sub_id)

    # This will fill participants.tsv table
    scan.sub_values["group"] = sub_row["Group"]
    scan.sub_values["sex"] = sub_row["Sex"]
    scan.sub_values["age"] = sub_row["Age"]
    scan.sub_values["education"] = sub_row["Education"]
    """

    if scan.subject in black_list and not black_list[scan.subject]:
        logger.info("Subject {} in black list".format(scan.subject))
        return -1


def SessionEP(scan: BidsSession) -> int:
    # Uncomment below if session should be renamed
    """
    ses_id = scan.session
    if ses_id.endswith("LCL"):
        scan.session = "ses-LCL"
    elif ses_id.endswith("HCL"):
        scan.session = "ses-HCL"
    else:
        # This will skip current session
        logger.error("Can't determine session from {}".format(ses_id))
        return -1
    """
    if scan.subject in black_list:
        if scan.session or scan.session in black_list[scan.subject]:
            logger.info("Session {} in black list".format(scan.session))
            return -1


def RecordingEP(recording: object):

    # Uncomment following if need to skip dummy volumes
    """
    rec_id = recording.recId()
    # Following will skip individual files
    # usefull for removing dummy volumes
    # Applicable only for MRI
    if recording.Module() == "MRI":
        if rec_id in task_prot:
            acq_N = recording.getAttribute("AcquisitionNumber")
            if acq_N <= n_dummies:
                return -1
    """


def SequenceEndEP(path, recording):
    if dry_run:
        # Nothing to do
        return 0

    # Uncomment following if need to merge Nifty into 4D
    """
    # Following will merge sequences in merge_4D into 4D
    # Applicable only for MRI and Nifty format
    if recording.Module() == "MRI":
        path = os.path.join(path, recording.getBidsSession().getPath(True),
                            recording.Module())
        for seq_dir in os.listdir(path):
            outfolder = os.path.join(path, seq_dir)
            if not os.path.isdir(outfolder):
                continue
            seq = seq_dir.split('-', 1)[1]
            if seq in merge_4D:
                logger.info('Merging fMRI from {}'.format(seq_dir))
                Convert3Dto4D(outfolder, recording)
    """


def SessionEndEP(session):
    if dry_run:
        # Nothing to do
        return 0

    # Removing acquisitions from remove_list
    cleanup_prepared(bidsfolder, session, remove_list)

    # Checking acquisition list
    check_prepared(bidsfolder, session, white_list)

    return 0


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


def cleanup_prepared(derivated, session, remove_list):
    """
    Cleanup unwanted sessions based on contents of remove_list
    """
    sub = session.subject
    ses = session.session if session.session else "ses-"

    for mod in remove_list:
        if sub not in remove_list[mod]:
            continue

        to_remove = remove_list[mod][sub]
        if isinstance(to_remove, dict):
            to_remove = to_remove.get(ses, [])
        elif ses == "ses-":
            if not isinstance(to_remove, list):
                logger.warning("Can't interpret {} as sequence to remove"
                               .format(to_remove))
            to_remove = []
        else:
            to_remove = []

        rm_path = os.path.join(derivated, session.getPath(empty=True), mod)
        for s in to_remove:
            pth = os.path.join(rm_path, s)
            if os.path.isdir(pth):
                logger.info("Removing {} from {}/{}".format(s, sub, ses))
                shutil.rmtree(pth)


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
