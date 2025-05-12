from enum import Enum


class PacketType(Enum):
    GCS_TO_AV_STATE_CMD = 0
    GSE_TO_GCS_DATA_1 = 1
    GSE_TO_GCS_DATA_2 = 2
    GSE_TO_GCS_DATA_3 = 3
    AV_TO_GCS_DATA_1 = 4
    AV_TO_GCS_DATA_2 = 5
    AV_TO_GCS_DATA_3 = 6
    GCS_TO_GSE_STATE_CMD = 7
