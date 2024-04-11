import os
import json

from bidsme.bidsMeta import BidsSession
from bidsme.plugins.tools.General import CheckSeries

# Will integrate plugin into logging
import logging
logger = logging.getLogger(__name__)

base_path = os.path.dirname(__file__)
base_path = os.path.join(base_path, "..")

# global variables
preparefolder = ""
bidsfolder = ""
dry_run = False

# Participants lists
white_list = {}
black_list = {}

acquisitions = {"ses-LCL": [
    "localizer",
    "cmrr_mbep2d_bold_mb2_invertpe",
    "cmrr_mbep2d_bold_mb2_task_nfat",
    "cmrr_mbep2d_bold_mb2_invertpe",
    "cmrr_mbep2d_bold_mb2_rest",
    "gre_field_mapping",
    "gre_field_mapping",
    "t1_mpr_sag_p2_iso",
    "t2_spc_da-fl_sag_p2_iso"
    ],
                "ses-HCL": [
    "localizer",
    "cmrr_mbep2d_bold_mb2_invertpe",
    "cmrr_mbep2d_bold_mb2_task_fat",
    "cmrr_mbep2d_bold_mb2_invertpe",
    "cmrr_mbep2d_bold_mb2_rest",
    "gre_field_mapping",
    "gre_field_mapping",
    "t1_mpr_sag_p2_iso",
    ]
                }

task_prot = ["cmrr_mbep2d_bold_mb2_task_nfat",
             "cmrr_mbep2d_bold_mb2_task_fat",
             "cmrr_mbep2d_bold_mb2_rest"
             ]


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
    w_pth = os.path.join(base_path, "white_list.json")
    if os.path.isfile(w_pth):
        logger.info("Loading wihte list from {}".format(w_pth))
        with open(w_pth) as f:
            white_list = json.load(f)

    b_pth = os.path.join(base_path, "black_list.json")
    if os.path.isfile(b_pth):
        logger.info("Loading black list from {}".format(b_pth))
        with open(b_pth) as f:
            black_list = json.load(f)


def SubjectEP(scan: BidsSession) -> int:
    if scan.subject in black_list and not black_list[scan.subject]:
        logger.info("Subject {} in black list".format(scan.subject))
        return -1


def SessionEP(session: BidsSession) -> int:
    path = os.path.join(preparefolder, session.getPath(True), "MRI")

    if session.subject in black_list and session.session in black_list[session.subject]:
        logger.info("Session {} in black list".format(session.session))
        return -1

    if session.subject in white_list and session.session in white_list[session.subject]:
        logger.info("Using alternative acquisitions from white list")
        acqs = white_list[session.subject][session.session]
    else:
        acqs = acquisitions[session.session]

    if not CheckSeries(path, acqs, strict=True):
        logger.error("{} Series do not match expectation."
                     .format(session.subject))
        return -1

    global series
    series = sorted(os.listdir(path))


def SequenceEP(recording):

    if recording.recId() == "cmrr_mbep2d_bold_mb2_invertpe":
        task_id = series.index(recording.recIdentity(index=False)) + 1
        if series[task_id].endswith("_task_nfat") or\
                series[task_id].endswith("_task_fat"):
            recording.custom["task"] = "sternberg"
        elif series[task_id].endswith("_rest"):
            recording.custom["task"] = "rest"
        else:
            logger.error("Can't retrieve task sequence for {}"
                         .format(recording.recIdentity()))
            return -1
    recording.custom["dummies"] = recording.getAttribute("AcquisitionNumber") - 1
