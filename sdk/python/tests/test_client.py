import unittest
import sys
import threading
from unittest.mock import MagicMock, patch

from runtime_rca import RuntimeRCA
from runtime_rca.exceptions import ConfigurationError


class RuntimeRCATests(unittest.TestCase):

    def setUp(self):
        self.rca = RuntimeRCA(
            api_key="test-api-key",
            service_name="payment-service",
            environment="testing",
        )

    def tearDown(self):
        self.rca.close()

    def test_client_initialization(self):
        self.assertEqual(
            self.rca.service_name,
            "payment-service",
        )

        self.assertEqual(
            self.rca.environment,
            "testing",
        )

    def test_api_key_is_required(self):
        with self.assertRaises(ConfigurationError):
            RuntimeRCA(
                api_key="",
                service_name="payment-service",
            )

    def test_service_name_is_required(self):
        with self.assertRaises(ConfigurationError):
            RuntimeRCA(
                api_key="test-key",
                service_name="",
            )

    def test_capture_exception_queues_event(self):
        with patch.object(
            self.rca.worker,
            "submit",
            return_value=True,
        ) as mock_submit:

            try:
                raise ValueError("Payment failed")

            except ValueError as error:
                result = self.rca.capture_exception(error)

            self.assertTrue(result)

            payload = mock_submit.call_args[0][0]

            self.assertEqual(
                payload["exception_type"],
                "ValueError",
            )

            self.assertIn(
                "Payment failed",
                payload["message"],
            )

            self.assertIn(
                "ValueError",
                payload["stack_trace"],
            )

    def test_capture_message_queues_event(self):
        with patch.object(
            self.rca.worker,
            "submit",
            return_value=True,
        ) as mock_submit:

            result = self.rca.capture_message(
                "Database connection failed"
            )

            self.assertTrue(result)

            payload = mock_submit.call_args[0][0]

            self.assertEqual(
                payload["message"],
                "Database connection failed",
            )

    def test_invalid_message_is_rejected(self):
        self.assertFalse(
            self.rca.capture_message("")
        )

    def test_background_worker_delivers_event(self):
        transport = MagicMock()

        from runtime_rca.worker import EventWorker

        worker = EventWorker(transport)

        try:
            result = worker.submit({
                "message": "Test event"
            })

            self.assertTrue(result)
            self.assertTrue(worker.flush(timeout=2))

            transport.send_event.assert_called_once()

        finally:
            worker.close()

    def test_transport_failure_does_not_crash_app(self):
        with patch.object(
            self.rca.worker,
            "submit",
            return_value=True,
        ):

            result = self.rca.capture_message(
                "Test network failure"
            )

            self.assertTrue(result)

    def test_main_thread_exception_hook(self):
        with patch("sys.excepthook") as previous_hook:
            with patch.object(self.rca, "capture_exception") as capture:
                with patch.object(self.rca, "flush"):
                    self.rca.install_exception_hooks()

                    try:
                        raise ValueError("Main thread crashed")
                    except ValueError as error:
                        sys.excepthook(
                            type(error),
                            error,
                            error.__traceback__,
                        )

                    capture.assert_called_once()
                    previous_hook.assert_called_once()

                    self.rca.uninstall_exception_hooks()

    def test_background_thread_exception_hook(self):
        with patch("threading.excepthook") as previous_hook:
            with patch.object(self.rca, "capture_exception") as capture:
                with patch.object(self.rca, "flush"):
                    self.rca.install_exception_hooks()

                    def failing_function():
                        raise ValueError("Background thread crashed")

                    thread = threading.Thread(target=failing_function)
                    thread.start()
                    thread.join()

                    capture.assert_called_once()
                    previous_hook.assert_called_once()

                    self.rca.uninstall_exception_hooks()

    def test_exception_hooks_can_be_installed_only_once(self):
        with patch("sys.excepthook") as previous_hook:
            self.rca.install_exception_hooks()
            self.rca.install_exception_hooks()

            self.assertIs(sys.excepthook, self.rca._sys_hook)
            self.assertIs(self.rca._previous_sys_hook, previous_hook)

            self.rca.uninstall_exception_hooks()

if __name__ == "__main__":
    unittest.main()
