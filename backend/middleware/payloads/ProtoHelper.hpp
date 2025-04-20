#pragma once
#define SET_PROTO_FIELD(proto, field) proto.set_##field(field())
#define SET_SUB_PROTO_FIELD(sub_proto, field) sub_proto->set_##field(field())