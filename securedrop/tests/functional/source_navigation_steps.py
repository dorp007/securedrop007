import tempfile
import time


class SourceNavigationStepsMixin:
    def _is_on_source_homepage(self):
        return self.wait_for(lambda: self.driver.find_element_by_id("source-index"))

    def _is_logged_in(self):
        return self.wait_for(lambda: self.driver.find_element_by_id("logout"))

    def _is_on_lookup_page(self):
        return self.wait_for(lambda: self.driver.find_element_by_id("source-lookup"))

    def _is_on_generate_page(self):
        return self.wait_for(lambda: self.driver.find_element_by_id("source-generate"))

    def _is_on_logout_page(self):
        return self.wait_for(lambda: self.driver.find_element_by_id("source-logout"))

    def _source_visits_source_homepage(self):
        self.driver.get(self.source_location)
        assert self._is_on_source_homepage()

    def _source_clicks_submit_documents_on_homepage(self, assert_success=True):

        # It's the source's first time visiting this SecureDrop site, so they
        # choose to "Submit Documents".
        self.safe_click_by_css_selector("#started-form button")

        if assert_success:
            # The source should now be on the page where they are presented with
            # a diceware codename they can use for subsequent logins
            assert self._is_on_generate_page()

    def _source_chooses_to_submit_documents(self):
        self._source_clicks_submit_documents_on_homepage()

        codename = self.driver.find_element_by_css_selector("#codename span")

        assert len(codename.text) > 0
        self.source_name = codename.text

    def _source_continues_to_submit_page(self, files_allowed=True):
        self.safe_click_by_css_selector("#create-form button")

        def submit_page_loaded():
            if not self.accept_languages:
                heading = self.driver.find_element_by_id("submit-heading")
                if files_allowed:
                    assert "Submit Files or Messages" == heading.text
                else:
                    assert "Submit Messages" == heading.text

        self.wait_for(submit_page_loaded)

    def _source_submits_a_file(self):
        with tempfile.NamedTemporaryFile() as file:
            file.write(self.secret_message.encode("utf-8"))
            file.seek(0)

            filename = file.name

            self.safe_send_keys_by_id("fh", filename)

            self.safe_click_by_css_selector(".form-controls button")
            self.wait_for_source_key(self.source_name)

            def file_submitted():
                if not self.accept_languages:
                    notification = self.driver.find_element_by_class_name("success")
                    expected_notification = "Thank you for sending this information to us"
                    assert expected_notification in notification.text

            # Allow extra time for file uploads
            self.wait_for(file_submitted, timeout=(self.timeout * 3))

            # allow time for reply key to be generated
            time.sleep(self.timeout)

    def _source_submits_a_message(
        self, verify_notification=False, first_submission=False, first_login=False
    ):
        self._source_enters_text_in_message_field()
        self.safe_click_by_css_selector(".form-controls button")

        def message_submitted():
            if not self.accept_languages:
                notification = self.driver.find_element_by_class_name("success")
                assert "Thank" in notification.text

                if verify_notification:
                    first_submission_text = (
                        "Please check back later for replies." in notification.text
                    )

                    if first_submission:
                        assert first_submission_text
                    else:
                        assert not first_submission_text

        self.wait_for(message_submitted)

        # allow time for reply key to be generated
        time.sleep(self.timeout)

    def _source_enters_text_in_message_field(self):
        self.safe_send_keys_by_id("msg", self.secret_message)

    def _source_logs_out(self):
        self.safe_click_by_id("logout")
        assert self._is_on_logout_page()
