from datalad.support.exceptions import IncompleteResultsError, CommandError
from filelock import Timeout, FileLock
from multiprocessing import Process
from pathlib import Path
from time import sleep
from typing import Union
from unittest.mock import Mock
import attr
import datalad.api as datalad
import datetime as dt
import logging
import os
import pytest
import random
import shutil
import tempfile

#from afni_test_utils import misc, tools
#from afni_test_utils.tools import get_current_test_name

DATA_FETCH_LOCK_PATH = Path(tempfile.gettempdir()) / "afni_tests_data.lock"
dl_lock = FileLock(DATA_FETCH_LOCK_PATH, timeout=300)


def get_tests_data_dir(dl_dset,dset_url=None,commit_ref=None):
    """Get the path to the test data directory. If the test data directory
    does not exist or is not populated, install with datalad.
    """
    logger = logging.getLogger("Test data setup")
    if not dl_dset.is_installed():
        if dl_dset.pathobj.exists():
            raise ValueError(
                f"{dl_dset.path} exists but is not a datalad repository"
            )
        else:
            try:
                global dl_lock
                dl_lock.acquire()
                if not dl_dset.is_installed():
                    logger.warn("Installing test data")
                    if not dset_url:
                        raise ValueError(
                            f"{dl_dset.path} is not installed and a url is not provided."
                        )
                    datalad.clone(
                        dset_url,
                        dl_dset.path,
                    )
            finally:
                dl_lock.release()

    # In the case where a datalad repository is read-only but the
    # correct git ref/commit is not checked out
    # we should raise an error
    if commit_ref is None:
        return
    else:
        raise NotImplementedError
    # confirm repo is user writable.
    some_files = [".git/logs/HEAD"]
    for f in some_files:
        data_file = dl_dset.pathobj / f
        if not data_file.exists():
            raise ValueError(
                f"{f} does not exist (parent existences: {f.parent.exists()}"
            )
        if not os.access(data_file, os.W_OK):
            raise ValueError(f"{f} is not user writeable ({os.getuid()})")


def check_file_exists(file_path, test_data_dir):
    full_path = test_data_dir / file_path
    no_file_error = (
        f"Could not find {full_path}. You have specified the path "
        f"{file_path} for an input datafile but this path does not exist "
        "in the test data directory that has been created in "
        f"{test_data_dir} "
    )

    if not (full_path.exists() or full_path.is_symlink()):
        if "sample_test_output" in full_path.parts:
            raise ValueError(
                "Cannot specify input data that is located in the "
                "sample_test_output directory. "
            )

        else:
            raise ValueError(no_file_error)


def generate_fetch_list(path_obj, test_data_dir):
    """Provided with path_obj, a list of pathlib.Path objects, resolves to a
    list containing 1 or more pathlib.Path objects.

    Args:
        path_obj (TYPE): may be a list of paths, a path, or a path that
    contains a glob pattern at the end
        test_data_dir (TYPE): Description

    Returns:
        List: List of paths as str type (including HEAD files if BRIK is used)
        Bool: needs_fetching, True if all data has not been downloaded

    Raises:
        TypeError: Description
    """
    needs_fetching = False
    fetch_list = []
    for p in path_obj:
        #        with_partners = add_partner_files(test_data_dir, p)
        #        for pp in with_partners:
        # fetch if any file does not "exist" (is a broken symlink)
        needs_fetching = needs_fetching or not (test_data_dir / p).exists()
        fetch_list.append(p)

    return [str(f) for f in fetch_list], needs_fetching


def glob_if_necessary(test_data_dir, path_obj):
    """
    Check that path/paths exist in test_data_dir. Paths  may be a
    glob, so tries globbing before raising an error that it doesn't exist. Return
    the list of paths.
    """
    if type(path_obj) == str:
        path_obj = [Path(path_obj)]
    elif isinstance(path_obj, Path):
        path_obj = [path_obj]
    elif iter(path_obj):
        path_obj = [Path(p) for p in path_obj]
    else:
        raise TypeError(
            "data_paths must contain paths (values that are of type str, pathlib.Path) or a "
            "non-str iterable type containing paths. i.e. list, tuple... "
        )

    outfiles = []

    for file_in in path_obj:

        try:
            # file should be found even if just as an unresolved symlink
            check_file_exists(file_in, test_data_dir)
            outfiles.append(file_in)
        except ValueError as e:
            outfiles += [f for f in (test_data_dir / file_in.parent).glob(file_in.name)]
            if not outfiles:
                raise e

    return outfiles


def add_partner_files(test_data_dir, path_in):
    """
    If the path is a brikor a head file the pair is returned for the purposes
    of fetching the data via datalad
    """
    try:
        from afnipy import afni_base as ab
    except ImportError:
        ab = misc.try_to_import_afni_module("afni_base")
    files_out = [path_in]
    brik_pats = [".HEAD", ".BRIK"]
    if any(pat in path_in.name for pat in brik_pats):
        parsed_obj = ab.parse_afni_name(str(test_data_dir / path_in))
        if parsed_obj["type"] == "BRIK":
            globbed = Path(parsed_obj["path"]).glob(parsed_obj["prefix"] + "*")
            files_out += list(globbed)
            files_out = list(set(files_out))

    return files_out


def process_path_obj(path_obj, test_data_dir, logger=None):
    """
    This function is used to process paths that have been defined in the
    data_paths dictionary of test modules. Globs are resolved, and the data is
    fetched using datalad. If HEAD files are provided, the corresponding BRIK
    files are also downloaded.

    Args: path_obj (str/pathlib.Path or iterable): Paths as
        strings/pathlib.Path  or non-str iterables with elements of these
        types can be passed as arguments for conversion to Path objects.
        Globbing at the final element of the path is also supported and will
        be resolved before being returned.

        test_data_dir (pathlib.Path): An existing datalad repository
        containing the test data.
    Returns:

        Iterable of Paths: Single pathlib.Path object or list of pathlib Paths
        fetched as required.
    """

    # Resolve all globs and return a list of pathlib objects
    path_obj = glob_if_necessary(test_data_dir, path_obj)
    # Search for any files that might be missing eg HEAD for a BRIK
    files_to_fetch, needs_fetching = generate_fetch_list(path_obj, test_data_dir)

    # Fetching the data
    if needs_fetching:
        attempt_count = 0
        while attempt_count < 2:
            # fetch data with a global dl_lock
            fetch_status = try_data_download(files_to_fetch, test_data_dir, logger)
            if fetch_status:
                break
            else:
                attempt_count += 1
        else:
            # datalad download attempts failed
            pytest.exit(
                f"Datalad download failed {attempt_count} times, you may "
                "not be connected to the internet "
            )
        if logger:
            logger.info(f"Downloaded data for {test_data_dir}")
    path_obj = [test_data_dir / p for p in path_obj]
    if len(path_obj) == 1:
        return path_obj[0]
    else:
        return path_obj


def try_data_download(file_fetch_list, test_data_dir, logger):
    try:
        global dl_lock
        dl_lock.acquire(poll_intervall=1)
        dl_dset = datalad.Dataset(str(test_data_dir))
        # Fetching the data
        process_for_fetching_data = Process(
            target=dl_dset.get, kwargs={"path": [str(p) for p in file_fetch_list]}
        )

        # attempts should be timed-out to deal with unpredictable stalls.
        process_for_fetching_data.start()
        # logger.debug(f"Fetching data for {test_data_dir}")
        process_for_fetching_data.join(timeout=60)
        if process_for_fetching_data.is_alive():
            # terminate the process.
            process_for_fetching_data.terminate()
            # logger.warn(f"Data fetching timed out for {file_fetch_list}")
            return False
        elif process_for_fetching_data.exitcode != 0:
            # logger.warn(f"Data fetching failed for {file_fetch_list}")
            return False
        else:
            return True
    except (
        IncompleteResultsError,
        ValueError,
        CommandError,
        TimeoutError,
        Timeout,
    ) as err:
        logger.warn(
            f"Datalad download failure ({type(err)}) for {test_data_dir}. Will try again"
        )

        return False

    finally:
        # make sure datalad repo wasn't updated to git annex version 8. Not sure why this is happening
        git_config_file = Path(test_data_dir) / ".git" / "config"
        git_config_file.write_text(
            git_config_file.read_text().replace("version = 8", "version = 7")
        )
        dl_lock.release()
        sleep(random.randint(1, 10))


