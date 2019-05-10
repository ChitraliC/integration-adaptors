from typing import List

import edifact.incoming.parser.creators as creators
from edifact.incoming.models.interchange import Interchange
from edifact.incoming.models.message import MessageSegment, Messages
from edifact.incoming.models.transaction import Transaction, Transactions
from edifact.incoming.parser import EdifactDict
import edifact.incoming.parser.helpers as helpers

INTERCHANGE_HEADER_KEY = "UNB"
MESSAGE_HEADER_KEY = "UNH"
MESSAGE_BEGINNING_KEY = "BGM"
MESSAGE_REGISTRATION_KEY = "S01"
MESSAGE_PATIENT_KEY = "S02"
MESSAGE_TRAILER_KEY = "UNT"
INTERCHANGE_TRAILER_KEY = "UNZ"


def deserialise_interchange_header(original_dict, index):
    interchange_header_line = EdifactDict(helpers.extract_relevant_lines(original_dict, index, [MESSAGE_HEADER_KEY]))
    interchange_header = creators.create_interchange_header(interchange_header_line)
    return interchange_header


def deserialise_message_beginning(original_dict, index):
    msg_bgn_lines = EdifactDict(helpers.extract_relevant_lines(original_dict, index, [MESSAGE_REGISTRATION_KEY]))
    msg_bgn_details = creators.create_message_segment_beginning(msg_bgn_lines)
    return msg_bgn_details


def deserialise_transaction(original_dict, index):
    transaction_pat = None
    transaction_lines = EdifactDict(
        helpers.extract_relevant_lines(original_dict, index + 1, [MESSAGE_REGISTRATION_KEY, MESSAGE_TRAILER_KEY]))

    msg_reg_lines = EdifactDict(helpers.extract_relevant_lines(transaction_lines, 0,
                                                       [MESSAGE_REGISTRATION_KEY, MESSAGE_PATIENT_KEY,
                                                        MESSAGE_TRAILER_KEY]))
    transaction_reg = creators.create_transaction_registration(msg_reg_lines)

    if len(msg_reg_lines) != len(transaction_lines):
        msg_pat_lines = EdifactDict(helpers.extract_relevant_lines(transaction_lines, len(msg_reg_lines),
                                                           [MESSAGE_REGISTRATION_KEY, MESSAGE_TRAILER_KEY]))
        transaction_pat = creators.create_transaction_patient(msg_pat_lines)

    transaction = Transaction(transaction_reg, transaction_pat)
    return transaction


def convert(lines: List[str]) -> Interchange:
    """
    Takes the original list of edifact lines and converts to a deserialised representation.
    Only relevant information from the edifact message is extracted and populated in the models.
    :param lines: A list of string of the edifact lines.
    :return: Interchange: The incoming representation of the edifact interchange.
    """
    original_dict = helpers.convert_to_dict(lines)
    messages = []
    transactions = []
    interchange = None
    interchange_header = None
    msg_bgn_details = None

    for index, line in enumerate(original_dict):
        key = line[0]

        if key == INTERCHANGE_HEADER_KEY:
            interchange_header = deserialise_interchange_header(original_dict, index)

        elif key == MESSAGE_BEGINNING_KEY:
            msg_bgn_details = deserialise_message_beginning(original_dict, index)

        elif key == MESSAGE_REGISTRATION_KEY:
            transaction = deserialise_transaction(original_dict, index)
            transactions.append(transaction)

        elif key == MESSAGE_TRAILER_KEY:
            msg = MessageSegment(msg_bgn_details, Transactions(transactions))
            messages.append(msg)
            transactions = []

        elif key == INTERCHANGE_TRAILER_KEY:
            interchange = Interchange(interchange_header, Messages(messages))

    return interchange
