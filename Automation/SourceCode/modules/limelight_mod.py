# pylint: disable=W0703,W0612,W0614,W0142,C0103,R0912,R0915,W0702,W0603,R0913
"""
#-------------------------------------------------------------------------------
# Name       :  limelight_mod
# Purpose    :  From glue code these functions will get called
# Author     :  Rebaca
# Created    :  18-03-2015
# Copyright  :  (c) Rebaca 2015
#-------------------------------------------------------------------------------
"""
import re
from modules.appium_driver import Driver
from modules.logger import info, error, warning
from modules.constant import *
from modules import exception_mod
from modules.OpenCvLib import OpenCvLibrary
from access_limelight_cms import limelightCMS

TAB_POINT = (100, 100)
NEXT_TAB_POINT = (100, 100)


class Limelight(Driver):
    """
    Limelight interface layer from here the main driver function will
    be called
    """
    def __init__(self):
        self.need_to_relaunch_app = False
        self.is_app_running = False
        super(Limelight, self).__init__(APPIUM_SERVER,
                                        TEST_TARGET_CFG['os'],
                                        TEST_TARGET_CFG['os-version'],
                                        TEST_TARGET_CFG['device-name'])

    @exception_mod.handle_exception
    def uncheck_delivery(self):
        """ Uncheck the delivery option if it is check """
        self.select_tab("PLAYER")
        ele_obj = self.get_element("check-box",
                                   generic_param=("Delivery",))
        if ele_obj.get_attribute('checked') == 'true':
            ele_obj.click()
        self.select_tab("SETTINGS")

    @exception_mod.handle_exception
    def launch_app(self):
        """
        Use to launch the application and create object of the main driver
        file
        """
        info("Launch the app.")
        try:
            self.set_up()
        except Exception as ex:
            reason = ex.__dict__.get('reason')
            reason = reason if reason else str(ex)
            error("App launch failed : %s" % str(reason))
            raise Exception(reason)
        self.is_app_running = True
        info("App Launched.")

    def exit_app(self):
        """ Use to tear down the application. """
        info("exit the app.")
        try:
            self.tear_down()
            self.wait_for(MEDIUM_WAIT)
            info("App Exited.")
        except Exception as ex:
            error(str(ex))
        finally:
            self.is_app_running = False

    @exception_mod.handle_exception
    def close_app(self):
        """ Use to close the application. """
        info("Close the app.")
        for i in range(4):
            self.driver.back()
        info("App Closed.")
        self.need_to_relaunch_app = True

    def set_orientation(self):
        """
        This will change the orientation to potrait mode
        if it is landscape
        """
        info("set orientation to potrait mode")
        change_from, change_to, out_put = self.rotate_device("PORTRAIT")
        #info("orientation changed from %s to %s" % (change_from, change_to))

    @exception_mod.handle_exception
    def select_tab(self, tab_name):
        """
        Select the tab whose name has been provided
        @arg:
            tab_name : display name of the tab
        """
        for ech_try in range(4):
            info("SELECT TAB => %s" % tab_name)
            if tab_name.lower().strip() == "current":
                pass
            else:
                # First move to the left most tab then start search
                if not self.is_item_visible(MAPPER[tab_name.lower()],
                                            generic_param=(tab_name, )) and \
                   not self.is_item_visible(MAPPER[LEFT_MOST_TAB.lower()],
                                            generic_param=(LEFT_MOST_TAB, )):
                    self.scrol_right_to_left(retry=1)
                # Now go to targeted tab
                self.click_on(MAPPER[tab_name.lower()], generic_param=(tab_name, ))

            info("SELECTED TAB => %s" % tab_name)
            try:
                self.scrol_bottom_to_top(retry=3)
            except Exception as exc:
                warning("While reset the scroll to top :%s" %  str(exc))
                if self.is_item_visible("setting-popup-cancel-btn"):
                    info("cancel button shown up, clicking on it")
                    self.click_on("setting-popup-cancel-btn")
                    continue
            break

    def get_element_details(self, element_name, generic_param=()):
        """
        Get the element details like width, height, coordinates etc.
        @args :
            element_name  : name of element (whose entry is in element-path.cfg)
                            or the element object
            generic_param : dynamic xpath/id variable
        """
        ele_obj = self.get_element(element_name,
                                   generic_param=generic_param)
        return {'width': int(ele_obj.size['width']),
                'height': int(ele_obj.size['height']),
                'x-coordinate': int(ele_obj.location['x']),
                'y-coordinate': int(ele_obj.location['y']),
                'obj': ele_obj
               }

    def perform_home_btn_press(self):
        """ Perform home key press """
        info("Perform home key press")
        global TAB_POINT
        global NEXT_TAB_POINT
        try:
            if TAB_POINT is None or NEXT_TAB_POINT is None:
                # some time after relaunching the application
                # GUI item is not accessible so we need to get the coordinate
                # tap
                tmp = self.get_element_details(MAPPER['media'],
                                               generic_param=("MEDIA", ))
                TAB_POINT = (tmp['x-coordinate'], tmp['y-coordinate'])
                tmp = self.get_element_details(MAPPER['player'],
                                               generic_param=("PLAYER", ))
                NEXT_TAB_POINT = (tmp['x-coordinate'], tmp['y-coordinate'])
        except Exception as ex:
            info("exception while getting the tap point:" + str(ex))
        self.native_key_press('HOME')

    def relaunch_app_frm_menu(self):
        """ Click on menu and then click on the application to launch it """
        if self.re_launch_limelight_app(TEST_TARGET_CFG['app-name']):
            self.wait_for_app_to_launch()
            info("App is re-launched")
            self.need_to_relaunch_app = False
        else:
            raise Exception("App not launched")

    def wait_for_app_to_launch(self):
        """
        Wait for the application to launch. sometime app takes time to launch
        """
        for ech_try in range(6):
            if not self.is_item_visible("app-title") or not self.is_item_visible("player"):
                info('Wait for app to launch')
                self.tap_on(*TAB_POINT)
                self.wait_for(MEDIUM_WAIT)
                self.tap_on(*NEXT_TAB_POINT)
                self.wait_for(MEDIUM_WAIT)
            else:
                info('App is launched')
                break
        else:
            info("App not launched")

    @exception_mod.handle_exception
    def refresh_tab(self, tab_name):
        """ Refresh a tab """
        info("REFRESH TAB => %s" % tab_name)
        self.refresh_by_pull_down()

    @exception_mod.handle_exception
    def scroll_down(self):
        """ Scroll down """
        self.refresh_by_pull_up()

    @exception_mod.handle_exception
    def set_select_value(self, tab_name, tel, operation, value):
        """
        Set/Select a particular element/value from a tab
        @args:
            tab_name      : name of the tab
            tel           : target element
            operation     : operation , set / select
            value            : set/select a value
        For searching :
            operation : search
            value : value to be search
            tel : search by
            tab_name : search in tab
        """
        info("%s value %s for %s ON %s tab" %
             (operation, value, tel, tab_name))

        self.select_tab(tab_name)

        # For settings page
        if "setting" in tab_name.lower():
            self.click_on("setting-elements-level", generic_param=(tel, ))
            info("Clicked => %s" % tel)
            if operation.lower().strip() == "set":
                self.should_visible("setting-popup-title")
                self.set_value("setting-popup-textbox", value)
                self.click_on('setting-popup-ok-btn')
            elif operation.lower().strip() == "select":
                self.should_visible("setting-popup-title")
                self.click_on("dropdown",
                              generic_param=(value, ))
            else:
                raise exception_mod.InvalidKeyWordUsed(operation=operation)

        # For channel groups page
        elif "channel groups" in tab_name.lower() or \
             "all channels" in tab_name.lower() or \
             "channels" in tab_name.lower() or \
             "all media" in tab_name.lower() or \
             "media" in tab_name.lower():
            if operation.lower().strip() == "select":
                self.click_on("data-list-item", generic_param=(value,))
            elif operation.lower().strip() == "search":
                # Click on the search text box
                self.click_on('search-input')
                # Provide the search data
                self.set_value('search-input', value)
                # Clicking on the go button
                self.click_on('search-go-btn')
                # Select the option
                self.click_on('search-options', generic_param=(tel,))
                # Click on ok button
                self.click_on('popup-button', generic_param=('Ok',))
                # wait till the progress bar gets hidden
                for ech_try in range(50):
                    try:
                        if self.is_item_visible('search-progress-bar') and \
                            not self.is_item_visible("error-message-in-tab"):
                            self.click_on('search-progress-bar')
                            info("media is still loading. retrying-> %s time"
                                 % ech_try)
                            self.wait_for(LONG_WAIT)
                        else:
                            info("the media is loaded")
                            break
                    except Exception as excp:
                        info(str(excp))
                        break
            else:
                raise exception_mod.InvalidKeyWordUsed(operation=operation)

        # For player page
        elif "player" in tab_name.lower():
            if operation.lower().strip() == "set":
                self.click_on(tel)
                self.set_value(tel, value)
            elif operation.lower().strip() == "select":
                self.click_on("data-list-item", generic_param=(value,))
            else:
                raise exception_mod.InvalidKeyWordUsed(operation=operation)
        else:
            raise exception_mod.GlueCodeNotImplemented

        info("DONE => %s value %s for %s ON %s" %
            (operation, value, tel, tab_name))

    @exception_mod.handle_exception
    def verify_value(self, tab_name, tel, value):
        """
        Verify a value for an element of a tab
        @args:
            tab_name : name of the tab that need to select
            tel      : target element
            value       : value that need to verify
        """
        info("CHECK VALUE => %s = %s" % (tel, value))
        if "setting" in tab_name.lower():
            self.value_should_be("setting-elements-level-op", value,
                                 generic_param=(tel,))
        info("DONE => %s = %s" % (tel, value))

    @exception_mod.handle_exception
    def perform_oper_on_tab(self, tab_name, oper):
        """ perform a operation on a tab
        @args:
            tab_name    :   name of the tab
            oper        :   operations - select / refresh / scroll-down
        """
        self.select_tab(tab_name)
        try:
            self.hide_keyboard()
            info("hide the android keyboard")
        except Exception as ex:
            info("cannot hide keyboard :: " + str(ex))
        if oper.strip().lower() == "select":
            pass
        elif oper.strip().lower() == "refresh":
            self.refresh_tab(tab_name)
        elif oper.strip().lower() == "scroll-down":
            self.scroll_down()
        else:
            raise exception_mod.GlueCodeNotImplemented

    @staticmethod
    def compare_two_list(list1, list2):
        """ List comparison helper function"""
        return reduce(lambda v1, v2: v1 and v2,
                      map(lambda ei: ei in list1, list2))

    @staticmethod
    def compare_two_list_find_diff(search_into_list, search_from_list, location=None):
        """ List comparison helper function"""
        if location is None:
            tmp_search_into_list = search_into_list[:]
            difference = []
            for ech_elm in search_from_list:
                if ech_elm in tmp_search_into_list:
                    tmp_search_into_list.remove(ech_elm)
                else:
                    difference.append(ech_elm)
            return difference == [], difference
        elif location.strip().lower() == "top":
            if search_into_list[:len(search_from_list)] == search_from_list:
                return True, []
            else:
                return False, search_from_list
        elif location.strip().lower() == "bottom":
            if search_into_list[-len(search_from_list):] == search_from_list:
                return True, []
            else:
                return False, search_from_list

    @exception_mod.handle_exception
    def check_icon(self, check_ele, verify_data, should_equal):
        """ To check the icon of any data """
        if check_ele.lower().strip().endswith(" tab"):
            tab_name = re.search(r"(\S+)\s+TAB", check_ele,
                                  flags=re.IGNORECASE).group(1)
            self.select_tab(tab_name)

            for element_text, icon_name in verify_data:
                info("checking : %s :: %s" % (element_text, icon_name))
                last_excp = ""
                for ech_try in range(3):
                    try:
                        scrn_sht_file = self.take_screenshot_of_element(
                                        "icon-of-item",
                                        (element_text, ))

                        stat = OpenCvLibrary.search_picture_in_picture(
                                        scrn_sht_file,
                                        os.path.join(ICON_DIR, icon_name))
                        if stat and should_equal:
                            info("icon matched: %s - %s" %
                                 (element_text, icon_name))
                        elif not stat and not should_equal:
                            info("icon not matched: %s - %s" %
                                 (element_text, icon_name))
                        elif should_equal:
                            raise Exception("icon not matched: %s - %s" %
                                            (element_text, icon_name))
                        elif not should_equal:
                            raise Exception("icon matched: %s - %s" %
                                            (element_text, icon_name))
                        try:
                            os.remove(scrn_sht_file)
                        except Exception as os_ex:
                            info("Not able to delete file :: %s" % str(os_ex))
                        break
                    except Exception as ex:
                        last_excp = str(ex)
                        info(last_excp + "--- Retrying")
                        self.wait_for(LONG_WAIT)
                else:
                    raise Exception(last_excp)

    @exception_mod.handle_exception
    def check_errors(self, check_ele, verify_data, should_equal):
        """
        Match the error message from device with the error message from
        feature file
        """
        # If we checking the data of a tab
        if check_ele.lower().strip().endswith(" tab"):
            tab_name = re.search(r"(\S+)\s+TAB", check_ele,
                                  flags=re.IGNORECASE).group(1)

            self.select_tab(tab_name)
            error_msg = ""
            for ech_try in range(1, 5):
                try:
                    error_msg = self.get_value("error-message-in-tab")
                    break
                except Exception as ex:
                    info(str(ex))
                    info("retrying %s wait for 2 secs" % ech_try)
                    self.wait_for(2)

            if error_msg.lower().strip() == verify_data[0].lower().strip() \
                and should_equal:
                info(exception_mod.equal_success_msg % error_msg)

            elif error_msg.lower().strip() != verify_data[0].lower().strip() \
              and not should_equal:
                info(exception_mod.not_equal_success_msg % (verify_data,
                                                            error_msg))
            elif should_equal:
                raise exception_mod.NotEqualException(verify_data, error_msg)

            else:
                raise exception_mod.EqualException(error_msg)

    @exception_mod.handle_exception
    def check_contains(self, check_ele, verify_data, should_equal, table_header,
                       location=None):
        """ match the data from device with the data from feature file"""
        if location not in [None, 'top', 'bottom']:
            raise Exception('invalid location given : %s' % location)
        print_msg = "check contains - check_ele=%s, verify_data=%s, " + \
                    "should_equal=%s, table_header=%s, location=%s"
        info(print_msg % (check_ele, verify_data, should_equal, table_header,
                          location))
        # If we checking the data of a tab
        if check_ele.lower().strip().endswith(" tab"):
            # ALL MEDIA TAB :: won't work for below expression
            '''
            tab_name = re.search( r"(\S+)\s+TAB", check_ele,
                                  flags=re.IGNORECASE).group(1)
            '''
            tab_name = check_ele.strip()[:-3].strip()
            self.select_tab(tab_name)

            if "control" in table_header:
                # search the ui element in the tab
                visible_element = []
                not_visible_element = []
                for each_element in verify_data:
                    if self.is_item_visible(each_element):
                        visible_element.append(each_element)
                    else:
                        not_visible_element.append(each_element)

                if should_equal:
                    # All elements should visible
                    if not_visible_element:
                        raise Exception("Elements not visible: %s" \
                                        % ', '.join(not_visible_element))
                    else:
                        info("visible : %s" % ', '.join(visible_element))
                else:
                    # All elements should not visible
                    if visible_element:
                        raise Exception("Elements visible: %s" %
                                        ', '.join(visible_element))
                    else:
                        info("not visible : %s" % ', '.join(not_visible_element))
            else:
                # Search the data
                for ech_try in range(4):
                    try:
                        data_got = self.scrol_top_to_bottom(ret_all_data=True)
                        break
                    except Exception as exc:
                        info(str(exc))
                        self.wait_for(LONG_WAIT)
                else:
                    raise Exception("failed to collect data from %s tab" %
                                    tab_name)

                data_got = [] if data_got is None else data_got
                stat, diff = self.compare_two_list_find_diff(data_got,
                                                             verify_data,
                                                             location)
                if should_equal and not stat:
                    raise exception_mod.NotEqualException(verify_data, data_got,
                                                          diff)
                elif not should_equal and stat:
                    raise exception_mod.EqualException(data_got)
                elif should_equal and stat:
                    info(exception_mod.equal_success_msg % data_got)
                elif not should_equal and not stat:
                    info(exception_mod.not_equal_success_msg % (verify_data,
                                                                data_got))
                else:
                    raise exception_mod.GlueCodeNotImplemented

        # If we checking the element of player
        elif check_ele.lower().strip() == "player":
            info("checking the player controls: %s" % ', '.join(verify_data))
            for ech_ele in verify_data:
                info("chk :: %s" % ech_ele)
                is_present = False
                for ech_try in range(4):
                    is_present = self.is_item_visible(ech_ele)
                    if not is_present:
                        self.wait_for(5)
                        self.click_on("player")
                    else:
                        break

                if is_present:
                    msg = "element: %s is present" % ech_ele
                else:
                    msg = "element: %s is not present" % ech_ele

                if is_present == should_equal:
                    info(msg)
                else:
                    raise Exception(msg)

        # If the checking the element of a popup
        elif check_ele.lower().strip() == "popup":
            data_got = self.scrol_top_to_bottom(ret_all_data=True,
                                                scroll_ele_typ="popup")
            data_got = [] if data_got is None else data_got
            stat, diff = self.compare_two_list_find_diff(data_got,
                                                         verify_data,
                                                         location)
            if should_equal and not stat:
                raise exception_mod.NotEqualException(verify_data, data_got,
                                                      diff)
            elif not should_equal and stat:
                raise exception_mod.EqualException(data_got)
            elif should_equal and stat:
                info(exception_mod.equal_success_msg % data_got)
            elif not should_equal and not stat:
                info(exception_mod.not_equal_success_msg % (verify_data,
                                                            data_got))
            else:
                raise exception_mod.GlueCodeNotImplemented

        # Checking the playlist
        elif check_ele.lower().strip() == "play-list":
            if "control" in table_header:
                # search the ui element in the play-list
                visible_element = []
                not_visible_element = []
                for each_element in verify_data:
                    if self.is_item_visible(each_element):
                        visible_element.append(each_element)
                    else:
                        not_visible_element.append(each_element)

                if should_equal:
                    # All elements should visible
                    if not_visible_element:
                        raise Exception("Elements not visible: %s" \
                                        % ', '.join(not_visible_element))
                    else:
                        info("visible : %s" % ', '.join(visible_element))
                else:
                    # All elements should not visible
                    if visible_element:
                        raise Exception("Elements visible: %s" %
                                        ', '.join(visible_element))
                    else:
                        info("not visible : %s" % ', '.join(not_visible_element))

    def go_to_tab_and_select_media(self, tab_name, media_name):
        """
        Select a tab then select the data of that tab
        @args:
            tab_name : name of the tab
            media_name : name of the media
        """
        self.select_tab(tab_name)
        self.set_select_value(tab_name, "", "select", media_name)

    def select_encoding(self, encoding_name, play_type):
        """
        Selects the encoding type
        @args:
            encoding_name : encoding-name/automatic/no-select
            play_type : local/remote
        """
        if play_type.strip().lower() == "local":
            if encoding_name.strip().lower() == "local":
                pass
            elif encoding_name.strip().lower() == "automatic":
                info("Select automatic encoding.")
                # Select the delivery check box
                self.click_on("check-box", generic_param=("Delivery",))
                # Click on the play button
                self.click_on("play-button")
        else:
            # Check if the choose encoding pop up is shown
            self.value_should_be("popup-title", "Choose Encoding")

            if encoding_name.strip().lower() == "no-select":
                # No need to select anything
                info("Not selecting any encoding.")
                return
            elif encoding_name.strip().lower() == "automatic":
                info("Select automatic encoding.")
                # Click on cancel button
                self.click_on("popup-button", generic_param=("Cancel", ))
                # Select the delivery check box
                self.click_on("check-box", generic_param=("Delivery", ))
                # Click on the play button
                self.click_on("play-button")
            else:
                # Click on the encoding element
                self.click_on("dropdown", generic_param=(encoding_name, ))

    def wait_for_alert_popup_close(self):
        """
        Wait for the alert popup get close
        """

        for i in xrange(30):
            try:
                if self.is_item_visible("alert-msg"):
                    info("%s :: alert popup still visible" %
                         self.get_value("alert-msg"))
                    self.wait_for(MEDIUM_WAIT)
                else:
                    info("alert popup is not visible")
                    break
            except Exception:
                break
        else:
            raise Exception("alert popup still visible")

    def wait_for_media_fetch(self):
        """
        Wait for the media fetched from the limelight server,
        Here we are checking if the progress bar has disabled or not
        """
        for i in xrange(30):
            try:
                if self.is_item_visible("alert-msg") and \
                    self.get_value("alert-msg") == FETCHING_MEDIA_MSG:
                    info("%s :: is still visible" % FETCHING_MEDIA_MSG)
                    self.wait_for(SORT_WAIT)
                else:
                    info("%s :: is not visible" % FETCHING_MEDIA_MSG)
                    break
            except Exception:
                break
        else:
            raise Exception("%s ::: msg still visible" % FETCHING_MEDIA_MSG)

    def wait_for_offline_download(self, encoding_name, play_type):
        """
        Wait for the off-line data gets downloaded
        Here we are checking if the progress bar has disabled or not
        @args:
            encoding_name : name of the selected encoding
            play_type     : local/remote
        """

        if play_type.strip().lower() == "local":
            return

        if encoding_name.strip().lower() == "automatic":
            strict_check = False
        elif "widevineoffline" in encoding_name.strip().lower():
            strict_check = True
        else:
            strict_check = None

        # For other cases we don't need to check this
        if strict_check is not None:
            for i in xrange(100):
                try:
                    if self.is_item_visible("alert-msg") and \
                       self.get_value("alert-msg") == \
                       WIDEVINE_OFFLINE_DOWNLOAD_MSG:
                        info("%s is visible" % WIDEVINE_OFFLINE_DOWNLOAD_MSG)
                        if strict_check:
                            strict_check = False
                        self.wait_for(MEDIUM_WAIT)
                    else:
                        info("%s not visible" % WIDEVINE_OFFLINE_DOWNLOAD_MSG)
                        # currently commented out this raise
                        #if strict_check:
                        #    raise Exception(exception_mod.widevine_error)
                        break
                except Exception as excp:
                    info(str(excp))
                    break
            else:
                raise Exception("%s ::: msg still visible" %
                                WIDEVINE_OFFLINE_DOWNLOAD_MSG)

    @exception_mod.handle_exception
    def perform_video_operations(self, opr, media_type, media_source,
                                 encoding_type):
        """
        @args:
            opr : play/pause/resume/seek-xx:xx/forwarded/
                  reversed/attempt-to-play
            media_type : local/remote/media-name
                         local -> Play from the memory card of the device
                         remote -> Play the remote url/media id
                         media-name -> if we want to play it from all
                                       media/media tab
            media_source : "menulink/file-name"/url/media-id/media-tab/
                           PLAY-LIST
            encoding_type : encoding-name/automatic/no-select
        """
        global SCENARIO_DATA

        ret_data = {'bfr_elapsed_time': None,
                    'aftr_elapsed_time': None,
                    'encoding_type': encoding_type,
                    'total_duration': None}

        info("Performing the video operations with parameters - ")
        pmsg = "operation=%s, media_type=%s, media_source=%s, encoding_type=%s"
        info(pmsg % (opr, media_type, media_source, encoding_type))

        if opr.strip().lower() == "play":

            # If play has passed then encoding_type should not "no-select"
            if encoding_type.lower().strip() == "no-select":
                msg = "for operation is %s, encoding should not %s" % \
                        (opr, encoding_type)
                raise exception_mod.InvalidCombination(**{'MSG': msg})

            # Local encoding type is for play a local file from SD card
            if encoding_type.lower().strip() == "local" and \
               media_type.strip().lower() != "local":
                msg = "local encoding is only when you play a local file"
                raise exception_mod.InvalidCombination(**{'MSG': msg})

            # For playing a local file then encoding should only be
            # 'automatic'/'local'
            if media_type.strip().lower() == "local" and \
               encoding_type.lower().strip() not in ['automatic', 'local']:
                msg = "To play a local file encoding should be automatic/local"
                raise exception_mod.InvalidCombination(**{'MSG': msg})

            skip_step = []
            if media_type.strip().lower() == "local":
                option_list = media_source.split("/")
                menue_link, file_name = option_list[:-1], option_list[-1]
                # Go to player tab
                self.select_tab("PLAYER")
                # Click on browse button
                self.click_on("browse-button")
                # Check on toggle menu button
                for tog_btn_entry in ["toggle-menu-button",
                                      "toggle-menu-button1",
                                      "toggle-menu-button2"]:
                    if self.is_item_visible(tog_btn_entry):
                        self.click_on(tog_btn_entry)
                        break
                    else:
                        info("%s not visible" % tog_btn_entry)
                else:
                    raise Exception("Not find the toggle button element," +
                                    "that specified in element config file")
                # Click on Downloads link
                for ech_side_link_entry in ["toggle-menu-left-side-links",
                                  "toggle-menu-left-side-links1"]:
                    if self.is_item_visible(ech_side_link_entry, generic_param=(menue_link[0],)):
                        self.click_on(ech_side_link_entry,
                                      generic_param=(menue_link[0],))
                        break
                else:
                    raise Exception("side menu not found")
                # Check alert title bar has text Downloads
                #self.value_should_be("local-file-browse-title", menue_link[0])
                self.wait_for(5)
                for ech_link in menue_link[1:]:
                    # Open the view menu on the right side

                    for ech_entry in ["local-video-view-menu-open-btn",
                                  "local-video-view-menu-open-btn1", 
                                  "local-video-view-menu-open-btn2"]:
                        if self.is_item_visible(ech_entry):
                            self.click_on(ech_entry)
                            break
                    else:
                        raise Exception("right side menu for grid/list view not found")

                    if self.is_item_visible("local-video-view-menu-option-link",
                                            generic_param=("List view",)):
                        info("List view option visible so clicking on it")
                        self.click_on("local-video-view-menu-option-link",
                                      generic_param=("List view",))
                    else:
                        # back so that the menu disappear
                        self.driver.back()


                    for ech_entry in ["file-link-in-menu", "file-link-in-menu1"]:
                        if self.is_item_visible(ech_entry, generic_param=(ech_link,)):
                            self.click_on(ech_entry, generic_param=(ech_link,))
                            break
                    else:
                        raise Exception("Not able to get the file link menu from GUI")

                # Click on the file
                for ech_entry in ["file-link-in-menu", "file-link-in-menu1"]:
                    if self.is_item_visible(ech_entry, generic_param=(file_name,)):
                        self.click_on(ech_entry, generic_param=(file_name,))
                        break
                else:
                    raise Exception("local video %s :: not found in expected path" % file_name)
                
                # Click The file name is came in search text box
                #self.value_should_contains("media-id-text-box", file_name)
                # failure

            elif media_type.strip().lower() == "remote":
                self.select_tab("PLAYER")
                info("Set url/media-id=%s" % media_source)
                # Set url/ media id
                self.set_select_value("PLAYER", "media-id-text-box",
                                      "set", media_source)
                # Click on the play button
                self.click_on("play-button")

            elif media_source.strip().lower() == "play-list":
                self.select_tab("PLAYER")
                info("select %s from playlist" % media_type)
                self.go_to_tab_and_select_media("CURRENT", media_type)
                skip_step = [2]

            else:
                info("Go to tab=%s and select media=%s" % (media_source,
                                                           media_type))
                # Go to a tab and select the media
                self.go_to_tab_and_select_media(media_source, media_type)

            # wait for any alert popup like settings is fetched from server
            if 1 not in skip_step:
                self.wait_for_alert_popup_close()

            # Select the encoding from drop down
            if 2 not in skip_step:
                self.select_encoding(encoding_type, media_type)

            # Check if the fetching media from server msg disappear
            if 3 not in skip_step:
                self.wait_for_media_fetch()

            # Check if the widevine download msg is displayer
            if 4 not in skip_step:
                self.wait_for_offline_download(encoding_type, media_type)

            # wait for any alert popup like widevine rights
            if 5 not in skip_step:
                self.wait_for_alert_popup_close()

            last_msg = ""
            for ech_try in range(10):
                if self.is_item_visible('player-elapsed-time'):
                    try:
                        ret_data['aftr_elapsed_time'] = \
                            self.get_value('player-elapsed-time')
                        ret_data['total_duration'] = \
                            self.get_value('player-video-duration')
                        break
                    except Exception as ex:
                        last_msg = str(ex)
                        info(last_msg)
                try:
                    self.click_on("player")
                except Exception as ex:
                    last_msg = str(ex)
                    info(last_msg)
                    self.wait_for(2)
                info("player elapsed time not found, retrying again")
            else:
                raise Exception(last_msg)

        elif opr.strip().lower() == "pause":
            is_btn_clieked = False
            for ech_try in range(10):
                # Check if the pause button is visible
                if not self.is_item_visible("player-pause-button"):
                    # Tap on the video player, if pause button isn't visible
                    self.click_on("player")
                try:
                    if not is_btn_clieked:
                        # We are taking the before elapse time only before
                        # clicking on pause button
                        ret_data['bfr_elapsed_time'] = \
                           self.get_value('player-elapsed-time')
                        # Click on the pause button
                        self.click_on("player-pause-button")
                        is_btn_clieked = True

                    ret_data['aftr_elapsed_time'] = \
                       self.get_value('player-elapsed-time')

                    ret_data['total_duration'] = \
                          self.get_value('player-video-duration')
                    break
                except Exception as ex:
                    warning(str(ex))
                    warning("pause button get invisible so quick")
                    continue
            else:
                raise Exception("not able to click on the pause button")

        elif opr.strip().lower() == "resume":
            is_btn_clieked = False
            for ech_try in range(10):
                # Check if the play button is visible
                if not self.is_item_visible("player-play-button"):
                    # Tap on video player, if play button is not visible
                    self.click_on("player")
                try:
                    if not is_btn_clieked:
                        # We are taking the before elapse time only before
                        # clicking on button
                        ret_data['bfr_elapsed_time'] = \
                            self.get_value('player-elapsed-time')
                        # Click on the play button
                        self.click_on("player-play-button")
                        is_btn_clieked = True
                    ret_data['aftr_elapsed_time'] = \
                        self.get_value('player-elapsed-time')
                    ret_data['total_duration'] = \
                        self.get_value('player-video-duration')
                    break
                except Exception as ex:
                    warning(str(ex))
                    warning("play button get invisible so quick")
                    continue

        elif opr.strip().lower() == "forwarded":
            is_btn_clieked = False
            for ech_try in range(10):
                # Check if the forward button is visible
                if not self.is_item_visible("player-forward-button"):
                    # Tap on video player, if forward button is not visible
                    self.click_on("player")
                try:
                    if not is_btn_clieked:
                        ret_data['bfr_elapsed_time'] = \
                          self.get_value('player-elapsed-time')
                        # Click on the forward button
                        self.click_on("player-forward-button")
                        is_btn_clieked = True
                    ret_data['aftr_elapsed_time'] = \
                      self.get_value('player-elapsed-time')
                    ret_data['total_duration'] = \
                          self.get_value('player-video-duration')
                    break
                except Exception as ex:
                    warning(str(ex))
                    warning("forward button get invisible so quick")
                    continue

        elif opr.strip().lower() == "reversed":
            is_btn_clieked = False
            info('collecting the elapse time before clicking reverse button')
            for i in range(4):
                try:
                    ret_data['bfr_elapsed_time'] = \
                        self.get_value('player-elapsed-time')
                    break
                except Exception as excp:
                    info(str(excp))
                    self.click_on('player')
            else:
                raise Exception("not able to collect the elapse time before clicking reverse button")
            info('collected elapse time as : %s' % ret_data['bfr_elapsed_time'])

            info("clicking reverse button")
            for i in range(4):
                try:
                    self.click_on("player-rewind-button")
                    break
                except Exception as excp:
                    info(str(excp))
                    self.click_on('player')
            else:
                raise Exception("not able to click reverse button")
            info("clicked reverse button")
            self.wait_for(2)

            info('collecting the elapse time after clicking reverse button')
            for i in range(4):
                try:
                    ret_data['aftr_elapsed_time'] = \
                        self.get_value('player-elapsed-time')
                    break
                except Exception as excp:
                    info(str(excp))
                    self.click_on('player')
            else:
                raise Exception("not able to collect the elapse time after clicking reverse button")
            info('collected elapse time as : %s' % ret_data['aftr_elapsed_time'])

            info('collecting the total duration of video')
            for i in range(4):
                try:
                    ret_data['total_duration'] = \
                          self.get_value('player-video-duration')
                    break
                except Exception as excp:
                    info(str(excp))
                    self.click_on('player')
            else:
                warning("not able to collect the total duration after clicking reverse button")
            info('collected total duration : %s' % ret_data['total_duration'])

        elif re.search(r"^seek-\d+:\d+$", opr.strip().lower()):
            is_btn_clieked = False
            seek_to_dur = opr.split("-")[1].split(':')
            seek_to_sec = int(seek_to_dur[0]) * 60 + int(seek_to_dur[1])
            for ech_try in range(10):
                # Check if the seek bar is visible
                if not self.is_item_visible("player-seekbar"):
                    # Tap on video player, if seek bar is not visible
                    self.click_on("player")
                try:
                    if not is_btn_clieked:
                        tot_vdo_dur = self.get_value("player-video-duration")\
                                      .split(':')
                        tot_vdo_sec = int(tot_vdo_dur[0]) * 60 + int(tot_vdo_dur[1])

                        ele_details = self.get_element_details("player-seekbar")
                        x_cal = (float(ele_details['width']) / tot_vdo_sec) \
                                * seek_to_sec
                        go_to_x = ele_details['x-coordinate'] + x_cal
                        go_to_x = int(round(go_to_x))
                        go_to_y = ele_details['y-coordinate']
                        ret_data['bfr_elapsed_time'] = \
                           self.get_value('player-elapsed-time')
                        # Seek the value
                        self.tap_on(go_to_x, go_to_y)
                        is_btn_clieked = True

                    ret_data['aftr_elapsed_time'] = \
                     self.get_value('player-elapsed-time')
                    ret_data['total_duration'] = \
                          self.get_value('player-video-duration')
                    break
                except Exception as ex:
                    warning(str(ex))
                    warning("seek bar get invisible so quick")
                    continue
        elif opr.strip().lower() == "completed": # TODO
            # Got the total video duration
            for ech_trn in range(4):
                try:
                    ret_data['total_duration'] = self.get_value("player-video-duration")
                    break
                except Exception as exc:
                    self.click_on("player")

            # Redefined the seeking duration
            dur = [int(ei) for ei in ret_data['total_duration'].split(':')]
            dur[0] -= 1
            seek_to = ('%2d:%2d'%(dur[0], dur[1])).replace(' ', '0')

            seek_to_dur = seek_to.split(':')
            seek_to_sec = int(seek_to_dur[0]) * 60 + int(seek_to_dur[1])

            tot_vdo_dur = ret_data['total_duration'].split(':')
            tot_vdo_sec = int(tot_vdo_dur[0]) * 60 + int(tot_vdo_dur[1])

            for ech_try in range(10):

                try:
                    ele_details = self.get_element_details("player-seekbar")
                    x_cal = (float(ele_details['width']) / tot_vdo_sec) * seek_to_sec
                    go_to_x = ele_details['x-coordinate'] + x_cal
                    go_to_x = int(round(go_to_x))
                    go_to_y = ele_details['y-coordinate']
                    ret_data['bfr_elapsed_time'] = self.get_value('player-elapsed-time')
                    # Seek the value
                    self.tap_on(go_to_x, go_to_y)
                    break
                except Exception as ex:
                    warning(str(ex))
                    warning("seek bar get invisible so quick")

            for ei in range(4):
                try:
                    ret_data['aftr_elapsed_time'] = self.get_value('player-elapsed-time')
                    break
                except:
                    self.click_on("player")

            elapse_vdo_dur = ret_data['aftr_elapsed_time'].split(':')
            elapse_vdo_sec = int(elapse_vdo_dur[0]) * 60 + int(elapse_vdo_dur[1])
            info("total : %s, current : %s" %(tot_vdo_sec, elapse_vdo_sec))
            self.wait_for(tot_vdo_sec - elapse_vdo_sec + 50)

            info("completed the video")

        elif opr.strip().lower() == "oldcompleted":
            num_of_retry = 10
            while num_of_retry > 0:
                try:
                    if not self.is_item_visible("player-video-duration"):
                        self.click_on("player")
                except Exception as ex:
                    info(str(ex))
                    num_of_retry -= 1
                    continue

                for ech_try in range(4):
                    try:
                        ret_data['total_duration'] = \
                          self.get_value("player-video-duration")
                        tot_vdo_dur = ret_data['total_duration'].split(':')
                        elp_vdo_dur = self.get_value('player-elapsed-time')\
                                        .split(':')
                        break
                    except Exception as ex:
                        info(str(ex))
                        self.click_on("player")
                else:
                    info("not able to get elapse time and total duration")
                    info("retrying")
                    continue

                tot_vdo_sec = int(tot_vdo_dur[0]) * 60 + int(tot_vdo_dur[1])
                elp_vdo_sec = int(elp_vdo_dur[0]) * 60 + int(elp_vdo_dur[1])
                num_of_forward = (tot_vdo_sec - elp_vdo_sec - 8)/15

                try:
                    if not self.is_item_visible("player-forward-button"):
                        self.click_on("player")
                except Exception as ex:
                    info(str(ex))
                    num_of_retry -= 1
                    continue

                for ech_forward in range(num_of_forward):
                    for etry in range(3):
                        try:
                            self.click_on("player-forward-button")
                            break
                        except:
                            self.click_on("player")

                if num_of_forward == 0:
                    rwait = tot_vdo_sec - elp_vdo_sec + 10
                    rwait = 0 if rwait < 1 else rwait
                    self.wait_for(rwait)
                    info("video playback completed")
                    break
                else:
                    self.wait_for(LONG_WAIT)

                try:
                    if not self.is_item_visible("player-video-duration"):
                        self.click_on("player")

                    if self.get_value("player-video-duration") == \
                       self.get_value('player-elapsed-time'):
                        info("video playback completed")
                        break
                except Exception as ex:
                    info(str(ex))
                    num_of_retry -= 1
                    continue

                # Retry again
                num_of_retry -= 1
            else:
                raise Exception("not able to complete the video playback")

        elif opr.strip().lower() == "attempt-to-play":
            # If attempt-to-play has passed then
            # encoding_type should be "no-select"
            if encoding_type.lower().strip() != "no-select":
                raise exception_mod.InvalidKeyWordUsed(**{
                    'encoding selection': encoding_type,
                    'operation': opr})

            if media_type.strip().lower() == "local":
                raise exception_mod.GlueCodeNotImplemented

            elif media_type.strip().lower() == "remote":
                # Set url/ media id
                self.set_select_value("PLAYER", "media-id-text-box",
                                      "set", media_source)
                # Click on the play button
                self.click_on("play-button")

            else:
                # Go to a tab and select the media
                self.go_to_tab_and_select_media(media_source, media_type)

            # Select the encoding from drop down
            self.select_encoding(encoding_type, media_type)

        else:
            raise exception_mod.InvalidKeyWordUsed(operation=opr)

        # For not selecting any element there should not be event save
        # Also for play list scenario we are not checking the events
        if encoding_type.strip().lower() != "no-select" and \
           media_source.strip().lower() != "play-list":
            if not self.is_item_visible("media-id-text-box"):
                info("The media id text box is not visible, " +
                     "so not able to store the events for the media")
            else:
                # Register the event for the action
                if media_type.lower().strip() != 'local':
                    # get the media id
                    media = self.get_value("media-id-text-box")
                else:
                    media = media_source.split("/")[-1]
                ky = (media, encoding_type)
                op_key_list = []
                opr = opr.lower().strip()
                if opr == "play":
                    op_key_list = ['player_loaded', 'play']
                elif opr == "pause":
                    op_key_list = ['pause']
                elif opr == "resume":
                    op_key_list = ['resume']
                elif 'seek-' in opr:
                    op_key_list = ['seek']
                elif opr == "completed":
                    op_key_list = ['completed']

                if SCENARIO_EVENT_KY not in SCENARIO_DATA:
                    SCENARIO_DATA[SCENARIO_EVENT_KY] = {}

                if ky not in SCENARIO_DATA["SCENARIO_WISE_PLAYER_EVENT"]:
                    SCENARIO_DATA["SCENARIO_WISE_PLAYER_EVENT"][ky] = {
                        'player_loaded': 0, 'play': 0, 'pause': 0, 'seek': 0,
                        'resume': 0, 'completed': 0
                    }
                for ech_op in op_key_list:
                    SCENARIO_DATA["SCENARIO_WISE_PLAYER_EVENT"][ky][ech_op] += 1

        return ret_data

    def verify_elapsed_time(self, duration, shud_diff=False):
        """
        Get elapsed time & match with passed duration
        @args:
            duration : the duration that need to verify
            shud_diff : True if it should difference else False
        """
        num_of_try = 0
        last_err = ""
        while num_of_try < 5:
            try:
                if not self.is_item_visible("player-elapsed-time"):
                    self.click_on('player')
                elapse_time = self.get_value("player-elapsed-time")
                break
            except Exception as ex:
                last_err = str(ex)
                info("error while getting elapsed time :: %s" % last_err)
                num_of_try += 1
                self.wait_for(SORT_WAIT)
        else:
            raise Exception(last_err)

        elapse_time_sec = elapse_time.split(':')
        elapse_time_sec = int(elapse_time_sec[0]) * 60 + int(elapse_time_sec[1])

        duration_sec = duration.split(':')
        duration_sec = int(duration_sec[0]) * 60 + int(duration_sec[1])
        if shud_diff:
            if 0 <= (elapse_time_sec - duration_sec) < 3:
                raise Exception("elapse-time: prev=%s, now=%s" % (duration,
                                                                  elapse_time))
            else:
                info("elapse-time: prev=%s, now=%s" % (duration, elapse_time))

        else:
            if -5 <= (elapse_time_sec - duration_sec) < 30:
                info("got elapse time=%s, passed %s" % (elapse_time,
                                                        duration))
            else:
                raise Exception("got elapse time=%s; expected=%s" %
                                (elapse_time, duration))

        return elapse_time

    def check_player_btn_icon(self, btn):
        """Take screen shot with player control bar & check given button icon"""
        img_btn = os.path.join(SCREEN_SHOT_DIR, "player_btn", "%s.png" % btn)
        info("chk img_btn %s present" % img_btn)
        screen_shot = self.tk_screen_shot_of_player(wth_plyr_cntrl=True)
        try:
            if OpenCvLibrary.search_picture_in_picture(screen_shot, img_btn):
                info("%s icon present in screen" % btn)
        except Exception as ex:
            error(str(ex))
            raise Exception("%s btn icon chk failed in screen." % btn)

    def tk_screen_shot_of_player(self, wth_plyr_cntrl, only_player=False):
        """
        Take the screen shot with or without player control
        @args:
            wth_plyr_cntrl : True  - Take screenshot with player control bar
                             False - Take screenshot without player control bar
            only_player    : True  - Take screenshot of player only
                             False - Take screenshot of full screen
        """
        if only_player:
            msg = "take screen shot of player"
        else:
            msg = "take screen shot of whole screen"
        info(msg)
        for ty in range(3):
            try:
                player_ele_data = self.get_element_details('player')
                break
            except Exception as ex:
                warning(str(ex))
                self.wait_for(MEDIUM_WAIT)
        else:
            raise Exception("not able to access player")

        if wth_plyr_cntrl:
            if not self.is_item_visible("player-controller-container"):
                self.click_on(player_ele_data['obj'])
        else:
            if self.is_item_visible("player-controller-container"):
                self.click_on(player_ele_data['obj'])
        if not self.is_item_visible("player-controller-container") and \
           wth_plyr_cntrl:
            self.click_on(player_ele_data['obj'])
        screen_shot = self.take_screenshot()
        if only_player:
            y1 = player_ele_data['y-coordinate']
            x1 = player_ele_data['x-coordinate']
            y2 = y1 + player_ele_data['height']
            x2 = x1 + player_ele_data['width']

            orientation_map = {'LANDSCAPE': (x1, x2, y1, y2),
                               'PORTRAIT': (y1, y2, x1, x2)}
            current_orientation = self.get_current_orientation()
            OpenCvLibrary.crop_file(screen_shot,
                                    *orientation_map[str(current_orientation)])
        return screen_shot

    def check_player_is_playing(self, data, skip_step=None):
        """
        @args :
              data    : data from previous grammar
              skip_step : the steps u want to skip
        Steps:
        1. Check pause button icon
        2. Take screen shot of the player without player control bar
        3. Wait for some time to take the next screen shot
        4. Take screen shot of whole screen without player control bar
        5. Verify the screen shots are different
        6. Check elapsed time has changed
        """
        sc_sht1 = sc_sht = ""
        skip_step = [] if skip_step is None else skip_step
        #bfr_elapsed_time = data['bfr_elapsed_time']
        aftr_elapsed_time = data['aftr_elapsed_time']
        if not aftr_elapsed_time:
            for et in range(3):
                try:
                    aftr_elapsed_time = self.get_value("player-elapsed-time")
                    break
                except:
                    self.click_on('player')

        if '1' not in skip_step:
            # Check pause button icon
            self.check_player_btn_icon('pause')

        if '2' not in skip_step:
            # Take screen shot of the player without player control bar
            sc_sht = self.tk_screen_shot_of_player(wth_plyr_cntrl=False,
                                                   only_player=True)

        if '3' not in skip_step:
            # Wait for some time to take the next screen shot
            self.wait_for(3)

        if '4' not in skip_step:
            # Take screen shot of whole screen without player control bar
            sc_sht1 = self.tk_screen_shot_of_player(wth_plyr_cntrl=False)

        if '5' not in skip_step:
            # Verify the screen shots are different
            if OpenCvLibrary.search_picture_in_picture(sc_sht1, sc_sht):
                msg = "screen-shots are same:: %s :: %s"
                raise Exception(msg % (sc_sht, sc_sht1))
            else:
                msg = "screen-shots are diff:: %s :: %s"
                info(msg % (sc_sht, sc_sht1))

        if '6' not in skip_step:
            # Check elapsed time has changed
            self.verify_elapsed_time(aftr_elapsed_time, shud_diff=True)

    def check_player_is_paused(self, data, skip_step=None):
        """
        @args :
              data    : data from previous grammar
              skip_step : the steps u want to skip
        Steps:
        1. Verify elapsed time, time should not change
        2. Check play button icon
        3. Take screen shot of the player without player control bar
        4. Wait for some time to take the next screen shot
        5. Take screen shot of whole screen without player control bar
        6. Verify the screen shots are same
        7. Check elapsed time has not changed

        """
        sc_sht1 = sc_sht = ""
        skip_step = [] if skip_step is None else skip_step
        bfr_elapsed_time = data['bfr_elapsed_time']
        aftr_elapsed_time = data['aftr_elapsed_time']

        if not bfr_elapsed_time:
            if not self.is_item_visible("player-elapsed-time"):
                self.click_on('player')
            bfr_elapsed_time = self.get_value("player-elapsed-time")
            self.wait_for(1)
            aftr_elapsed_time = None

        if not aftr_elapsed_time:
            if not self.is_item_visible("player-elapsed-time"):
                self.click_on('player')
            aftr_elapsed_time = self.get_value("player-elapsed-time")

        # Verify elapsed time, time should not change
        if '1' not in skip_step:
            info('verify elapsed time, time should not change')
            bfr_elapsed_time_sec = bfr_elapsed_time.split(':')
            bfr_elapsed_time_sec = int(bfr_elapsed_time_sec[0]) * 60 + \
                                    int(bfr_elapsed_time_sec[1])
            aftr_elapsed_time_sec = aftr_elapsed_time.split(':')
            aftr_elapsed_time_sec = int(aftr_elapsed_time_sec[0]) * 60 + \
                                    int(aftr_elapsed_time_sec[1])
            if (aftr_elapsed_time_sec - bfr_elapsed_time_sec) > 3:
                msg = "on click pause btn elapse time not stop." + \
                      " prev: %s, after: %s"
                raise Exception(msg % (bfr_elapsed_time, aftr_elapsed_time))
            else:
                msg = "on click pause btn elapse time stop." + \
                      " prev: %s, after: %s"
                info(msg % (bfr_elapsed_time, aftr_elapsed_time))

        # Check play button icon
        if '2' not in skip_step:
            self.check_player_btn_icon('play')

        # Take screen shot without player control bar
        if '3' not in skip_step:
            sc_sht = self.tk_screen_shot_of_player(wth_plyr_cntrl=False,
                                                   only_player=True)

        # Wait for some time to take the next screen shot
        if '4' not in skip_step:
            self.wait_for(3)

        # Take screen shot of whole screen without player control bar
        if '5' not in skip_step:
            sc_sht1 = self.tk_screen_shot_of_player(wth_plyr_cntrl=False)

        # Verify the screen shots are same
        if '6' not in skip_step:
            info("verify screen shots are same")
            if OpenCvLibrary.search_picture_in_picture(sc_sht1, sc_sht):
                info("screen shots are same: %s :: %s" % (sc_sht, sc_sht1))
            else:
                raise Exception("screen shots are not same: %s :: %s" % (sc_sht,
                                                                       sc_sht1))

        # Check elapsed time has not changed
        if '7' not in skip_step:
            self.verify_elapsed_time(aftr_elapsed_time, shud_diff=False)

    def check_player_is_resumed(self, data, skip_step=None):
        """
        @args :
              data : data from previous grammar
        Steps:
        1. Check pause button icon
        2. Take screen shot of the player without player control bar
        3. Wait for some time to take the next screen shot
        4. Take screen shot of whole screen without player control bar
        5. Verify the screen shots are different
        6. Check elapsed time has changed
        """
        skip_step = [] if skip_step is None else skip_step
        #bfr_elapsed_time = data['bfr_elapsed_time']
        #aftr_elapsed_time = data['aftr_elapsed_time']
        self.check_player_is_playing(data, skip_step=skip_step)

    def check_player_is_forwarded(self, data, state, skip_step=None):
        """
        @args :
              data    : data from previous grammar
              state   : play/pause
        Steps:
        1. Verify elapsed time, time is move forward with a certain range
        2. Check pause/play button icon according to player state
        3. Take screen shot of the player without player control bar
        4. Wait for some time to take the next screen shot
        5. Take screen shot of whole screen without player control bar
        6. verify the screen shot are different/same according to player state
        7. Check elapsed time has changed/remain same according to play/pause
        """
        skip_step = [] if skip_step is None else skip_step
        bfr_elapsed_time = data['bfr_elapsed_time']
        aftr_elapsed_time = data['aftr_elapsed_time']

        # Verify elapsed time, time is move forward with a certain range
        info('verify elapsed time, time is move forward with a certain range')
        bfr_elapsed_time_sec = bfr_elapsed_time.split(':')
        bfr_elapsed_time_sec = int(bfr_elapsed_time_sec[0]) * 60 + \
                               int(bfr_elapsed_time_sec[1])
        aftr_elapsed_time_sec = aftr_elapsed_time.split(':')
        aftr_elapsed_time_sec = int(aftr_elapsed_time_sec[0]) * 60 + \
                                int(aftr_elapsed_time_sec[1])
        if FORWARD_SEC <= (aftr_elapsed_time_sec - bfr_elapsed_time_sec) \
           < FORWARD_SEC + 7:
            msg = "on click forward btn elapse time change as expect." + \
                  " prev: %s, after: %s"
            info(msg % (bfr_elapsed_time, aftr_elapsed_time))
        else:
            msg = "on click forward btn elapse time don't change as expect." + \
                  " prev: %s, after: %s"
            raise Exception(msg % (bfr_elapsed_time, aftr_elapsed_time))

        # perform the steps according to state : play/pause
        if state == 'play':
            self.check_player_is_playing(data, skip_step=skip_step)
        else:
            skip_step.append('1')
            self.check_player_is_paused(data, skip_step=skip_step)

    def check_player_is_reversed(self, data, state, skip_step=None):
        """
        @args :
              data    : data from previous grammar
              state   : play/pause
        Steps:
        1. Verify elapsed time, time is move backwards with a certain range
        2. Check pause/play button icon according to player state
        3. Take screen shot of the player without player control bar
        4. Wait for some time to take the next screen shot
        5. Take screen shot of whole screen without player control bar
        6. verify the screen shot are different/same according to player state
        7. Check elapsed time has changed/remain same according to play/pause
        """
        skip_step = [] if skip_step is None else skip_step
        bfr_elapsed_time = data['bfr_elapsed_time']
        aftr_elapsed_time = data['aftr_elapsed_time']

        # Verify elapsed time, time is move backward with a certain range
        info('verify elapsed time, time is move backward with a certain range')
        bfr_elapsed_time_sec = bfr_elapsed_time.split(':')
        bfr_elapsed_time_sec = int(bfr_elapsed_time_sec[0]) * 60 + \
                               int(bfr_elapsed_time_sec[1])
        aftr_elapsed_time_sec = aftr_elapsed_time.split(':')
        aftr_elapsed_time_sec = int(aftr_elapsed_time_sec[0]) * 60 + \
                                int(aftr_elapsed_time_sec[1])
        ## Reverse cause move back
        if -REVERSE_SEC <= (aftr_elapsed_time_sec - bfr_elapsed_time_sec) < \
           -REVERSE_SEC + 15:
            msg = "on click reverse btn elapse time change as expect." + \
                  " prev: %s, after: %s"
            info(msg % (bfr_elapsed_time, aftr_elapsed_time))
        else:
            msg = "on click reverse btn elapse time don't change as expect." + \
                  " prev: %s, after: %s"
            raise Exception(msg % (bfr_elapsed_time, aftr_elapsed_time))

        # perform the steps according to state : play/pause
        if state == 'play':
            self.check_player_is_playing(data, skip_step=skip_step)
        else:
            skip_step.append('1')
            self.check_player_is_paused(data, skip_step=skip_step)

    def check_player_is_seeking(self, duration, data, state, skip_step=None):
        """
        @args :
              duration: duration that passed from front end
              data    : data from previous grammar
              state   : play/pause
        Steps:
        1. Verify elapsed time, aftr_elapsed_time ~= duration
        2. Check pause/play button icon according to player state
        3. Take screen shot of the player without player control bar
        4. Wait for some time to take the next screen shot
        5. Take screen shot of whole screen without player control bar
        6. verify the screen shot are different/same according to player state
        7. Check elapsed time has changed/remain same according to play/pause
        """
        skip_step = [] if skip_step is None else skip_step
        aftr_elapsed_time = data['aftr_elapsed_time']

        # Verify elapsed time, aftr_elapsed_time ~= duration
        info('verify elapsed time, aftr_elapsed_time ~= duration')
        duration_sec = duration.split(':')
        duration_sec = int(duration_sec[0]) * 60 + int(duration_sec[1])
        aftr_elapsed_time_sec = aftr_elapsed_time.split(':')
        aftr_elapsed_time_sec = int(aftr_elapsed_time_sec[0]) * 60 + \
                                int(aftr_elapsed_time_sec[1])
        ## Reverse cause move back
        if abs(aftr_elapsed_time_sec - duration_sec) < 50:
            msg = "verify elapsed time is seek to time." + \
                  " elapsed time: %s, duration: %s"
            info(msg % (aftr_elapsed_time, duration))
        else:
            msg = "verify failed elapsed time is seek time." + \
                  " elapsed time: %s, duration: %s"
            raise Exception(msg % (aftr_elapsed_time, duration))

        # perform the steps according to state : play/pause
        if state == 'play':
            self.check_player_is_playing(data, skip_step=skip_step)
        else:
            skip_step.append('1')
            self.check_player_is_paused(data, skip_step=skip_step)

    @exception_mod.handle_exception
    def check_player(self, operation, vdo_src_typ, duration,
                     player_state, ret_data, chk_full_screen):
        """
        @args :
              operation   : operations - play/pause/resume/continue-playing/
                            remain-pause/seek/forwarded/reversed/not play
              vdo_src_typ : Source of play - file/url/mediaId/media-tab
              duration    : Duration of play (min:sec)
              player_state: State of the player - play/pause
              ret_data    : Previous grammar data
        """
        # As we are checking the player so we should not check this
        # for not play mode
        if operation.lower().strip() != "not play":
            # Check the player mode
            in_full_screen = self.is_player_in_full_screen_mode()
            if chk_full_screen and not in_full_screen:
                # Check the player is in full screen mode
                raise Exception("player is in normal mode")
            elif not chk_full_screen and in_full_screen:
                # Check the player is in normal mode
                raise Exception("player is in full screen mode")
            else:
                info("player screen mode as expected full screen : %s " % in_full_screen)

        if operation.lower().strip() == "play" and \
           player_state.lower().strip() == "play":
            ## '''Checking play'''
            # For protected content skip image comparison
            if ("widevine" in ret_data['encoding_type'].lower()) or \
               ("automatic" in ret_data['encoding_type'].lower() and
                 vdo_src_typ.lower().strip() != "file"):
                skip_step = ['2', '4', '5']
            else:
                skip_step = []
            self.check_player_is_playing(ret_data, skip_step=skip_step)

        elif operation.lower().strip() == "pause" and \
           player_state.lower().strip() == "pause":
            ## '''Checking pause'''
            # For protected content skip image comparison
            if ("widevine" in ret_data['encoding_type'].lower()) or \
               ("automatic" in ret_data['encoding_type'].lower() and
                 vdo_src_typ.lower().strip() != "file"):
                skip_step = ['3', '5', '6']
            else:
                skip_step = []
            self.check_player_is_paused(ret_data, skip_step=skip_step)

        elif operation.lower().strip() == "resume" and \
            player_state.lower().strip() == "play":
            ## '''Checking resume'''
            # For protected content skip image comparison
            if ("widevine" in ret_data['encoding_type'].lower()) or \
               ("automatic" in ret_data['encoding_type'].lower() and
                vdo_src_typ.lower().strip() != "file"):
                skip_step = ['2', '4', '5']
            else:
                skip_step = []
            self.check_player_is_resumed(ret_data, skip_step=skip_step)

        elif operation.lower().strip() == "forwarded":
            ## '''Checking forwarded with play/pause state'''
            # For protected content skip image comparison
            if ("widevine" in ret_data['encoding_type'].lower()) or \
               ("automatic" in ret_data['encoding_type'].lower() and
                vdo_src_typ.lower().strip() != "file"):
                if player_state.lower().strip() == "play":
                    skip_step = ['2', '4', '5']
                else:
                    skip_step = ['3', '5', '6']
            else:
                skip_step = []

            self.check_player_is_forwarded(ret_data,
                                           player_state.lower().strip(),
                                           skip_step=skip_step)

        elif operation.lower().strip() == "reversed":
            ## '''Checking reversed with play/pause state'''
            # For protected content skip image comparison
            if ("widevine" in ret_data['encoding_type'].lower()) or \
               ("automatic" in ret_data['encoding_type'].lower() and
                vdo_src_typ.lower().strip() != "file"):
                if player_state.lower().strip() == "play":
                    skip_step = ['2', '4', '5']
                else:
                    skip_step = ['3', '5', '6']
            else:
                skip_step = []

            self.check_player_is_reversed(ret_data,
                                           player_state.lower().strip(),
                                           skip_step=skip_step)

        elif operation.lower().strip() == "seek":
            ## '''Checking seek'''
            # For protected content skip image comparison
            if ("widevine" in ret_data['encoding_type'].lower()) or \
               ("automatic" in ret_data['encoding_type'].lower() and
                 vdo_src_typ.lower().strip() != "file"):
                if player_state.lower().strip() == "play":
                    skip_step = ['2', '4', '5']
                else:
                    skip_step = ['3', '5', '6']
            else:
                skip_step = []
            self.check_player_is_seeking(duration, ret_data,
                                         player_state.lower().strip(),
                                         skip_step=skip_step)

        elif operation.lower().strip() == "continue-playing":
            ## '''Checking play'''
            # For protected content skip image comparison
            if ("widevine" in ret_data['encoding_type'].lower()) or \
               ("automatic" in ret_data['encoding_type'].lower() and
                 vdo_src_typ.lower().strip() != "file"):
                skip_step = ['2', '4', '5']
            else:
                skip_step = []
            self.check_player_is_playing(ret_data, skip_step=skip_step)

        elif operation.lower().strip() == "remain-pause":
            ## Checking pause
            # For protected content skip image comparison
            if ("widevine" in ret_data['encoding_type'].lower()) or \
               ("automatic" in ret_data['encoding_type'].lower() and
                 vdo_src_typ.lower().strip() != "file"):
                skip_step = ['3', '5', '6']
            else:
                skip_step = []
            self.check_player_is_paused(ret_data, skip_step=skip_step)

        elif operation.lower().strip() == "not play" and \
           player_state.lower().strip() == "play":
            # Check the encoding list should not shown up
            got_encoding_popup = False
            try:
                self.value_should_be("popup-title", "Choose Encoding")
                got_encoding_popup = True
            except Exception:
                pass
            if got_encoding_popup:
                raise Exception("encoding list has been shown up")
            # Check the player doesn't loaded
            for ech_try in range(5):
                if self.is_item_visible("player"):
                    raise Exception("Player is loaded")
                else:
                    self.wait_for(SORT_WAIT)
            info("Player does not load")

    @exception_mod.handle_exception
    def perform_device_operations(self, action_itm, perform, target):
        """
        @args :
              action_itm : home-button/app-icon/screen
              perform    : press/orientation
              target     : application/device
              For No-internet :
                action_itm : internet
                perform    : on/off
                target     : device
        """
        if action_itm == 'home-button' and perform == "press" and \
           target == "application":
            self.perform_home_btn_press()
        elif action_itm == 'app-icon' and perform == "press" and \
           target == "device":
            self.relaunch_app_frm_menu()
        elif action_itm == 'screen' and perform == "orientation" and \
           target == "device":
            self.rotate_device()
        elif action_itm == 'internet' and perform in ["on", "off"] and \
           target == "device":
            self.switch_internet_connection(perform)
        else:
            exception_mod.InvalidCombination(action_itm=action_itm,
                                             perform=perform,
                                             target=target)

    def add_to_playlist(self, target, media_names=None, tab_name=None):
        """
        @args :
        target      : following / all
        media_names  : [] -> a list of media name
        tab_name    : tab name of the app

        Steps:
        1. Go to that tab

        If need to add selective media then:
         2. Click on the the add to playlist button for each media that has been
         passed from feature file.

        If need to add all media:
         3. click on the "Add All To Playlist" button
        """
        for et in range(4):
            # Step 1
            self.select_tab(tab_name)
            # Step 2
            if target == "all" and not media_names:
                self.click_on("add-all-to-playlist-btn")
            elif target == "following" and media_names:
                for ech_media_name in media_names:
                    try:
                        self.click_on("add-to-playlist-btn", (ech_media_name, ))
                        if self.is_item_visible("popup-button", ("Cancel", )):
                            self.click_on("popup-button", ("Cancel", ))
                            info("encode popup shown so retry again")
                            break  # Retry from outer loop
                    except Exception as ex:
                        info(str(ex))
                        self.wait_for_alert_popup_close()
                        break  # Retry from outer loop
                    try:
                        self.scrol_bottom_to_top(retry=3)
                    except Exception as exc:
                        warning("While reset the scroll to top :%s"%str(exc))
                else:
                    break
                # Continue if anything goes wrong.
                # if break out from inner loop
                info("something went wrong so again retrying to perform the steps")
                continue
            else:
                raise exception_mod.InvalidCombination(target=target,
                                                       media_names=media_names)
            # For normal case break out from retry
            break

    def remove_from_playlist(self, target, media_names=None, tab_name=None):
        """
        @args :
        target      : following / all
        media_names : [] -> a list of media name
        tab_name    : tab name of the app

        Steps:
        1. Go to that tab

        If need to remove selective media then:
         2. Click on the the remove button for each media that has been
         passed from feature file.

        If need to add all media:
         3. click on the remove button for all media
        """
        # Step 1
        self.select_tab(tab_name)
        self.scrol_bottom_to_top(retry=8)
        # Step 2
        if target == "all" and not media_names:
            while True:
                try:
                    self.scrol_bottom_to_top(retry=8)
                except:
                    pass

                try:
                    data = self.scrol_top_to_bottom(ret_all_data=True)
                except Exception as ex:
                    info(str(ex))
                    break
                if not data:
                    break

                info("resetting the scroll")
                self.scrol_bottom_to_top(retry=8)
                info("resetting the scroll done")
                remove_item = []
                try:
                    for ech_media_name in data:
                        if ech_media_name in remove_item:
                            continue
                        remove_item.append(ech_media_name)
                        self.click_on("remove-from-playlist-btn",
                                      (ech_media_name, ))
                        try:
                            self.scrol_bottom_to_top(retry=8)
                        except:
                            pass
                    info("items removed: %s" % remove_item)
                except Exception as ex:
                    info(str(ex))
                    self.wait_for_alert_popup_close()

        elif target == "following" and media_names:
            for ech_media_name in media_names:
                for ech_try in range(4):
                    self.click_on("remove-from-playlist-btn", (ech_media_name, ))
                    if self.is_item_visible("remove-from-playlist-btn", (ech_media_name, )):
                        continue
                    if self.is_item_visible("alert-msg"):
                        self.wait_for_alert_popup_close()  # For fetching
                        self.wait_for_alert_popup_close()  # for downloading
                        continue
                    break
                try:
                    self.scrol_bottom_to_top()
                except:
                    pass
        else:
            raise exception_mod.InvalidCombination(target=target,
                                                   media_names=media_names)

    @exception_mod.handle_exception
    def add_delete_from_playlist(self, operation, target, tab_name, add_item_name, add_type):
        """
        @args :
        operation : add / remove
        target    : following / all
        tab_name  : tab name of the app
        media_name  : [] -> a list of media name
        add_type : media/channel
        """
        if operation == "add" and target == "all" and add_type == 'media':
            # perform steps to add all media in playlist, only for media
            self.add_to_playlist(target, tab_name=tab_name)
        elif operation == "add" and target == "following":
            # perform steps to add following media from feature file in playlist
            if not add_item_name:
                raise exception_mod.InvalidCombination(target=target,
                                                       media_name=add_item_name)
            if add_type == 'channel':
                # Click on the channel
                self.select_tab(tab_name)
                self.click_on("data-list-item", generic_param=(add_item_name[0],))

            self.add_to_playlist(target, add_item_name, tab_name)
            if add_type == 'channel':
                # Click on the channel auto play
                for i in range(30):
                    try:
                        self.click_on("autoplay-checkbox")
                        break
                    except Exception as exc:
                        info(str(exc))
                        self.wait_for(LONG_WAIT)

        elif operation == "remove" and target == "all":
            # perform steps to remove all media in playlist
            self.remove_from_playlist(target, tab_name=tab_name)
        elif operation == "remove" and target == "following":
            # perform steps to remove provided media from feature file to
            # playlist
            if not add_item_name:
                raise exception_mod.InvalidCombination(target=target,
                                                       media_name=add_item_name)
            self.remove_from_playlist(target, add_item_name, tab_name)
        else:
            raise exception_mod.InvalidCombination(operation=operation,
                                                    target=target,
                                                    tab_name=tab_name,
                                                    media_name=add_item_name)

    @exception_mod.handle_exception
    def verify_add_delete_from_playlist(self, operation, target,
                                        source_tab_name, playlist_tab_name,
                                        media_name):
        """
        @args :
        target    : following / all
        source_tab_name : The tabe name feom where we are adding the media
                          This is very important while verifying the add all
                          scenario
        operation : added / removed
        playlist_tab_name  : tab name of the app that contains the playlist
        media_name  : [] -> a list of media name
        """
        if operation == "added" and target == "all":
            # Steps :
            # 1. Go to tab source_tab_name
            self.select_tab(source_tab_name)
            # 2. Get all media name those are present in that tab
            self.scrol_bottom_to_top(retry=8)
            source_media_list = self.scrol_top_to_bottom(retry=4,
                                                         ret_all_data=True)
            self.scrol_bottom_to_top(retry=8)  # reset the screen
            # 3. Go to tab playlist_tab_name
            self.select_tab(playlist_tab_name)
            # 4. Get all media that present in playlist
            self.scrol_bottom_to_top(retry=8)
            playlist_data = self.scrol_top_to_bottom(retry=4,
                                                     ret_all_data=True)
            self.scrol_bottom_to_top(retry=8)  # reset the screen

            # 5. Verify that all media from source tab is present in playlist
            for ech_media_name in source_media_list:
                if ech_media_name in playlist_data:
                    info("media %s -- present" % ech_media_name)
                else:
                    raise Exception("media %s -- not present" % ech_media_name)
            info("All media from %s tab is present in playlist" %
                 source_tab_name)

        elif operation == "added" and target == "following":
            if not media_name:
                raise exception_mod.InvalidCombination(target=target,
                                                       media_name=media_name)
            # Steps :
            # 1. Go to tab playlist_tab_name
            self.select_tab(playlist_tab_name)

            # 2. Get all media that present in playlist
            self.scrol_bottom_to_top(retry=8)
            playlist_data = self.scrol_top_to_bottom(retry=4,
                                                     ret_all_data=True)
            self.scrol_bottom_to_top(retry=8)  # reset the screen

            # 3. Verify that all media from feature file is present in playlist
            info(playlist_data)
            for ech_media_name in media_name:
                if ech_media_name in playlist_data:
                    info("media %s -- present" % ech_media_name)
                else:
                    raise Exception("media %s -- not present" % ech_media_name)

            info("All media from feature file is present in playlist")

        elif operation == "removed" and target == "all":
            # Steps :
            # 1. Go to tab playlist_tab_name
            self.select_tab(playlist_tab_name)
            # 2. Get all media that present in playlist
            playlist_data = []
            if self.is_item_visible("playlist-container"):
                self.scrol_bottom_to_top(retry=8)
                playlist_data = self.scrol_top_to_bottom(retry=4,
                                                         ret_all_data=True)
                self.scrol_bottom_to_top(retry=8)  # reset the screen

            # 3. Verify that all media has removed
            if playlist_data:
                raise Exception("all media has not removed from play list")
            else:
                info("all media has removed from play list")

        elif operation == "removed" and target == "following":
            # Steps :
            # 1. Go to tab playlist_tab_name
            self.select_tab(playlist_tab_name)
            # 2. Get all media that present in playlist
            playlist_data = []
            if self.is_item_visible("playlist-container"):
                self.scrol_bottom_to_top(retry=8)
                playlist_data = self.scrol_top_to_bottom(retry=4,
                                                         ret_all_data=True)
                self.scrol_bottom_to_top(retry=8)  # reset the screen
            # 3. Verify that all media from feature file doesn't present
            #    in playlist
            for ech_media_name in media_name:
                if ech_media_name not in playlist_data:
                    info("media %s :: not present" % ech_media_name)
                else:
                    raise Exception("media %s :: present" % ech_media_name)

            info("All media from feature file doesn't present in playlist")

        else:
            raise exception_mod.InvalidCombination(target=target,
                                            source_tab_name=source_tab_name,
                                            operation=operation,
                                            playlist_tab_name=playlist_tab_name,
                                            media_name=media_name)

    @exception_mod.handle_exception
    def check_notification(self, notification_type):
        """
        This will check the expected notification
        @args :
        notification_type : StartSession/Play/Pause/Seek/MediaComplete/expected
         (expected : it will search the number of play pause seek etc operation
          in this scenario and try to match with those)
          :: currently implementation has been done only for "expected" keyword
        """
        if notification_type.lower().strip() == "expected":
            msg = ""
            for ech_ky, ech_val in SCENARIO_DATA.get(SCENARIO_EVENT_KY,
                                                     {}).iteritems():
                msg += "For %s expected value = %s ; " % \
                       (str(ech_ky), str(ech_val))
            raise exception_mod.NotEqualException(msg, "")

    @exception_mod.handle_exception
    def check_playlist_oper(self, oper, which_media, duration, state, ret_data):
        """
        """
        info("chk play list operation. oper: " +
             "%s, media: %s, duration:%s, state:%s, ret_data:%s" %
             (oper, which_media, duration, state, ret_data))
        self.wait_for_alert_popup_close()
        if oper.strip().lower() == "play":
            elapsed_time = None
            tot_duration = None
            for ei in range(4):
                try:
                    if not self.is_item_visible("player-elapsed-time"):
                        self.click_on('player')
                    elapsed_time = self.get_value("player-elapsed-time")\
                                   .split(':')
                    elapsed_time = int(elapsed_time[0]) * 60 + int(elapsed_time[1])
                    tot_duration = self.get_value("player-video-duration")
                    break
                except Exception as ex:
                    info(str(ex))

            if elapsed_time is None:
                raise Exception("Not able to get elapsed time")
            if tot_duration is None:
                raise Exception("Not able to get total duration of the video")
            info("elapse time :: %s" % elapsed_time)
            info("video duration ::> previous = %s :: current = %s" %
                 (ret_data['total_duration'], tot_duration))
            if 70 > elapsed_time >= 0 and \
              tot_duration != ret_data['total_duration']:
                info("player start playing from begning")
                info("player playing different duration video")
                self.check_player_is_playing({'bfr_elapsed_time': None,
                                              'aftr_elapsed_time': None},
                                              skip_step=[2, 3, 4, 5])
            else:
                raise Exception("player doesn't start playing from beginning" +
                                " or the player doesn't play a different video")

    @exception_mod.handle_exception
    def perform_playlist_video_oper(self, oper, media_name, auto_playlist):
        """
        """
        global SCENARIO_DATA

        ret_data = {'bfr_elapsed_time': None,
                    'aftr_elapsed_time': None,
                    'encoding_type': 'automatic',
                    'total_duration': None}

        info("Performing the play list video operations with parameters - ")
        pmsg = "operation=%s, media_type=%s, media_source=%s, encoding_type=%s"
        info(pmsg % (oper, media_name, 'play list', 'automatic'))

        self.select_tab("PLAYER")

        if auto_playlist.strip().lower() == "on":
            # Check the auto playlist option
            ele_obj = self.get_element("autoplay-checkbox")
            if ele_obj.get_attribute('checked') != 'true':
                ele_obj.click()
        else:
            # uncheck the auto playlist option
            ele_obj = self.get_element("autoplay-checkbox")
            if ele_obj.get_attribute('checked') == 'true':
                ele_obj.click()

        if oper.strip().lower() == "play":
            #skip_step = []
            info("select %s from playlist" % media_name)
            self.go_to_tab_and_select_media("PLAYER", media_name)
            # wait for any alert popup like settings is fetched from server
            self.wait_for_alert_popup_close()
            # Check if the fetching media from server msg disappear
            self.wait_for_media_fetch()
            # Check if the widevine download msg is displayer
            self.wait_for_offline_download('automatic', media_name)
            # wait for any alert popup like widevine rights
            self.wait_for_alert_popup_close()

            last_msg = ""
            for ech_try in range(10):
                if self.is_item_visible('player-elapsed-time'):
                    try:
                        ret_data['aftr_elapsed_time'] = \
                            self.get_value('player-elapsed-time')
                        ret_data['total_duration'] = \
                            self.get_value('player-video-duration')
                        break
                    except Exception as ex:
                        last_msg = str(ex)
                        info(last_msg)
                try:
                    self.click_on("player")
                except Exception as ex:
                    last_msg = str(ex)
                    info(last_msg)
                    self.wait_for(2)
                info("player elapsed time not found, retrying again")
            else:
                raise Exception(last_msg)

        return ret_data

    def is_player_in_full_screen_mode(self):
        """
        return True if player in full screen mode
        """
        if self.is_item_visible("player"):
            # The player is visible
            if self.is_item_visible("horizontal-scroll"):
                # The player is in normal mode
                return False
            else:
                # The player is in full screen mode
                return True
        else:
            raise Exception("Player is not visible")

    def switch_full_screen(self, full_screen_state):
        """
        full_screen_state : on - to do full screen
                            of - to exit full screen
        """
        if full_screen_state not in ['on', 'off']:
            raise Exception("full_screen_state: on/off, found %s" %
                             full_screen_state)

        in_full_screen = self.is_player_in_full_screen_mode()

        if (not in_full_screen and full_screen_state == 'on') or \
           (in_full_screen and full_screen_state == 'off'):
            # Change either to full screen mode or normal mode
            for echtry in range(3):
                try:
                    self.click_on("full-screen-button")
                    break
                except Exception as ex:
                    info(str(ex))
                    self.click_on("player")
            else:
                raise Exception("Not able to click on full screen button")

            if in_full_screen:
                info("Change the player to normal mode")
            else:
                info("Change the player to full screen mode")
        else:
            if in_full_screen:
                info("Player already is in full screen mode")
            else:
                info("Player already is in normal screen mode")

    @exception_mod.handle_exception
    def perform_player_operation(self, action_itm, perform):
        """
            For full screen:
            action_itm : full-screen
            perform    : on/off
            For player next and previous button click:
            action_itm : player-next-button/player-previous-button
            perform    : click

        """
        ret_data = {}

        if action_itm == "full-screen":
            self.switch_full_screen(full_screen_state=perform)
        elif perform == "click":
            ret_data = {'bfr_elapsed_time': None,
                    'aftr_elapsed_time': None,
                    'encoding_type': 'automatic',
                    'total_duration': None}
            for ei in range(4):
                try:
                    if not ret_data['bfr_elapsed_time']:
                        ret_data['bfr_elapsed_time'] = \
                          self.get_value('player-elapsed-time')

                    if not ret_data['total_duration']:
                        ret_data['total_duration'] = \
                          self.get_value('player-video-duration')
                    break
                except Exception as ex:
                    self.click_on("player")

            for ech_try in range(5):
                try:
                    self.click_on(str(action_itm))
                    break
                except Exception as exc:
                    info("While click on "+action_itm+"::"+str(exc))
                    self.click_on('player')
            else:
                raise Exception("not able to click on %s"% action_itm)

            self.wait_for_alert_popup_close()

            for ei in range(4):
                try:
                    ret_data['aftr_elapsed_time'] = \
                      self.get_value('player-elapsed-time')
                    break
                except Exception as ex:
                    self.click_on("player")
        else:
            raise exception_mod.GlueCodeNotImplemented

        return ret_data

    @exception_mod.handle_exception
    def update_media(self, media_name, param_name, new_val):
        """
        @args :
        new_val : new value
        param_name : name of the parameter that need to update
        media_name : media name
        """
        cms = limelightCMS()
        if param_name.lower().strip() == 'state':
            try:
                cms.setMediaState(media_name, new_val)
            except Exception as ex:
                raise Exception("error while updating state of media :" + str(ex))
        else:

            try:
                cms.updateMedia(media_name, param_name, new_val)
            except Exception as ex:
                raise Exception("error while updating the media :" + str(ex))
        self.wait_for(LONG_WAIT*5)

    def switch_internet_connection(self, perform):
        """
        if perform = on :: switch on the internet
        if perform = off :: switch off the internet
        """
        if perform == 'off':
            self.disconnect_from_network()
        elif perform == 'on':
            self.reconnect_to_network()
        else:
            raise Exception("unknown keywork %s for internet on/off" % perform)

