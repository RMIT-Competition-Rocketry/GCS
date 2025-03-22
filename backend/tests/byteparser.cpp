#include <gtest/gtest.h>
#include "../middleware/payloads/ByteParser.hpp"

// Note that all GCS calls so far are in BIG_ENDIAN byte order

TEST(ByteParserTest, ExtractBitsBigEndian)
{
    uint8_t data[] = {0b11001100, 0b10101010};
    ByteParser parser(data, sizeof(data), ByteOrder::BIG_ENDIAN_ORDER);

    EXPECT_EQ(parser.extract_bits(4), 0b1100);
    EXPECT_EQ(parser.extract_bits(4), 0b1100);
    EXPECT_EQ(parser.extract_bits(8), 0b10101010);
}