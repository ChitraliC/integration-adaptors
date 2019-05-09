import unittest
from pathlib import Path
from builder.pystache_message_builder import PystacheMessageBuilder
from utilities.file_utilities import FileUtilities
from utilities.xml_utilities import XmlUtilities
from OneOneOne.OneOneOne.message_handler import MessageHandler

from definitions import ROOT_DIR


class MessageHandlerTest(unittest.TestCase):
    expectedXmlFileDir = Path(ROOT_DIR) / 'OneOneOne' / 'tests' / 'expected_output_xmls'
    inputXmlFileDir = Path(ROOT_DIR) / 'OneOneOne' / 'tests' / 'input_xmls'

    def test_action_not_matching_service(self):
        builder = PystacheMessageBuilder(str(self.inputXmlFileDir), 'action_does_not_match_service')

        with self.subTest("Two differing services result in a 500 error"):
            service_dict = {'action': "urn:nhs-itk:services:201005:SendNHS111Report-v2-0-ThisDoesNotMatchBelow",
                            'service': "urn:nhs-itk:services:201005:SendNHS111Report-Bad_Service-ThisDoesNotMatchAbove"}

            msg = builder.build_message(service_dict)
            mh = MessageHandler(msg)
            status_code, response = mh.check_action_types()

            assert (status_code == 500)

            expected = FileUtilities.get_file_string(
                str(self.expectedXmlFileDir / 'invalid_action_service_values_response.xml'))
            XmlUtilities.assert_xml_equal_utf_8(expected, response)

        with self.subTest("Two services which are the same should return 200 code"):
            service_dict = {'action': "urn:nhs-itk:services:201005:SendNHS111Report",
                            'service': "urn:nhs-itk:services:201005:SendNHS111Report"}

            msg = builder.build_message(service_dict)
            mh = MessageHandler(msg)
            status_code, response = mh.check_action_types()

            assert (status_code == 200)

    def test_manifest_payload_count(self):
        builder = PystacheMessageBuilder(str(self.inputXmlFileDir), 'manifest_payload_count')

        with self.subTest("Mismatched counts: 500 response"):
            counts = {'manifestCount': "2",
                      'payloadCount': "5"}

            msg = builder.build_message(counts)
            mh = MessageHandler(msg)
            status_code, response = mh.check_manifest_and_payload_count()

            assert (status_code == 500)

            expected = FileUtilities.get_file_string(
                str(self.expectedXmlFileDir / 'manifest_not_equal_to_payload_count.xml'))
            XmlUtilities.assert_xml_equal_utf_8(expected, response)

        with self.subTest("Equal counts: 200 response"):
            counts = {'manifestCount': "2",
                      'payloadCount': "2"}

            msg = builder.build_message(counts)
            mh = MessageHandler(msg)
            status_code, response = mh.check_manifest_and_payload_count()

            assert (status_code == 200)

    def test_manifest_count_matches_manifest_instances(self):
        builder = PystacheMessageBuilder(str(self.inputXmlFileDir), 'manifest_count_manifest_instances')

        with self.subTest("Incorrect manifest occurrences returns 500 error"):
            manifests = {'manifestCount': "2",
                         'manifest': [{"id": 'one'}]}

            msg = builder.build_message(manifests)
            mh = MessageHandler(msg)
            status_code, response = mh.check_manifest_count_against_actual()

            assert (status_code == 500)

            expected = FileUtilities.get_file_string(
                str(self.expectedXmlFileDir / 'invalid_manifest_instances.xml'))
            XmlUtilities.assert_xml_equal_utf_8(expected, response)

        with self.subTest("Correct manifest occurrences returns 500 error"):
            manifests = {'manifestCount': "1",
                         'manifest': [{"id": 'one'}]}

            msg = builder.build_message(manifests)
            mh = MessageHandler(msg)
            status_code, response = mh.check_manifest_count_against_actual()

            assert (status_code == 200)

    def test_payload_count_against_instances(self):
        builder = PystacheMessageBuilder(str(self.inputXmlFileDir), 'payload_count')

        with self.subTest("Incorrect manifest occurrences returns 500 error"):
            manifests = {'payloadCount': "2",
                         'payloads': [{"id": 'one'}]}

            msg = builder.build_message(manifests)
            mh = MessageHandler(msg)
            status_code, response = mh.check_payload_count_against_actual()

            assert (status_code == 500)

            expected = FileUtilities.get_file_string(
                str(self.expectedXmlFileDir / 'basic_fault_response.xml'))
            XmlUtilities.assert_xml_equal_utf_8(expected, response)

        with self.subTest("Incorrect manifest occurrences returns 500 error"):
            manifests = {'payloadCount': "1",
                         'payloads': [{"id": 'one'}]}

            msg = builder.build_message(manifests)
            mh = MessageHandler(msg)
            status_code, response = mh.check_payload_count_against_actual()

            assert (status_code == 200)

    def test_payload_id_matches_manifest_id(self):
        builder = PystacheMessageBuilder(str(self.inputXmlFileDir), 'payload_manifest_ids')

        with self.subTest("Incorrect manifest occurrences returns 500 error"):
            dictionary = {'payloadCount': "2",
                          'payloads': [{"id": 'one'}, {"id": 'three'}],
                          'manifestCount': "2",
                          'manifests': [{"id": 'one'}, {"id": 'two'}]
                          }

            msg = builder.build_message(dictionary)
            mh = MessageHandler(msg)

            status_code, response = mh.check_payload_id_matches_manifest_id()
            assert (status_code == 500)

            expected = FileUtilities.get_file_string(
                str(self.expectedXmlFileDir / 'payloadID_does_not_match_manifestID.xml'))
            XmlUtilities.assert_xml_equal_utf_8(expected, response)

            with self.subTest("Incorrect manifest occurrences returns 500 error"):
                dictionary = {'payloadCount': "2",
                              'payloads': [{"id": 'one'}],
                              'manifestCount': "2",
                              'manifests': [{"id": 'one'}]
                              }

                msg = builder.build_message(dictionary)
                mh = MessageHandler(msg)

                status_code, response = mh.check_payload_id_matches_manifest_id()
                assert (status_code == 200)
