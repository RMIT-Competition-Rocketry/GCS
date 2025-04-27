#include "../middleware/payloads/ByteParser.hpp"

#include <gtest/gtest.h>

// Note that all GCS calls in 0.1.0 are big-endian.
// Little-endian will be used in futture packet revisions.

// --------- TEST: .extract_unsigned_bits ---------
// ----------------------------------------

TEST(ByteParserExtractUBitsTest, ExtractBitsBig1) {
  uint8_t data[] = {0b11001100};
  ByteParser parser(data, sizeof(data), ByteOrder::BIG_ENDIAN_ORDER);

  EXPECT_EQ(parser.extract_unsigned_bits(8), 204U);
}

TEST(ByteParserExtractUBitsTest, ExtractBitsBig2) {
  uint8_t data[] = {0b11111111};
  ByteParser parser(data, sizeof(data), ByteOrder::BIG_ENDIAN_ORDER);

  EXPECT_EQ(parser.extract_unsigned_bits(8), 255U);
}

TEST(ByteParserExtractUBitsTest, ExtractBitsBigPartial) {
  uint8_t data[] = {0b11001100, 0b10101010};
  ByteParser parser(data, sizeof(data), ByteOrder::BIG_ENDIAN_ORDER);

  EXPECT_EQ(parser.extract_unsigned_bits(4), 12U);
  EXPECT_EQ(parser.extract_unsigned_bits(4), 12U);
  EXPECT_EQ(parser.extract_unsigned_bits(8), 170U);
}

TEST(ByteParserExtractUBitsTest, ExtractBitsNothing) {
  uint8_t data[] = {0b11001100, 0b10101010};
  ByteParser parser(data, sizeof(data), ByteOrder::BIG_ENDIAN_ORDER);

  EXPECT_EQ(parser.extract_unsigned_bits(0), 0U);
  EXPECT_EQ(parser.extract_unsigned_bits(16), 52394U);
}

TEST(ByteParserExtractUBitsTest, OverExtract) {
  uint8_t data[] = {0b11001100};
  ByteParser parser(data, sizeof(data), ByteOrder::BIG_ENDIAN_ORDER);

  EXPECT_EQ(parser.extract_unsigned_bits(8), 204U);
  EXPECT_THROW(parser.extract_unsigned_bits(1), std::out_of_range);
}

TEST(ByteParserExtractUBitsTest, OverRequestValidData) {
  uint8_t data[] = {0b11001100, 0b11001100, 0b11001100, 0b11001100, 0b11001100};
  ByteParser parser(data, sizeof(data), ByteOrder::BIG_ENDIAN_ORDER);

  EXPECT_THROW(parser.extract_unsigned_bits(48), std::out_of_range);
  EXPECT_EQ(parser.extract_unsigned_bits(32), 3435973836U);
  EXPECT_EQ(parser.extract_unsigned_bits(8), 204U);
}

TEST(ByteParserExtractUBitsTest, OverRequestOverLimit) {
  uint8_t data[] = {0b11011100};
  ByteParser parser(data, sizeof(data), ByteOrder::BIG_ENDIAN_ORDER);

  EXPECT_THROW(parser.extract_unsigned_bits(33), std::out_of_range);
  EXPECT_EQ(parser.extract_unsigned_bits(8), 220U);
}

TEST(ByteParserExtractUBitsTest, OverRequestData) {
  uint8_t data[] = {0b11001100};
  ByteParser parser(data, sizeof(data), ByteOrder::BIG_ENDIAN_ORDER);

  EXPECT_THROW(parser.extract_unsigned_bits(16), std::out_of_range);
  EXPECT_EQ(parser.extract_unsigned_bits(8), 204U);
}

TEST(ByteParserExtractUBitsTest, OverRequestData2) {
  uint8_t data[] = {0b11001100};
  ByteParser parser(data, sizeof(data), ByteOrder::BIG_ENDIAN_ORDER);

  EXPECT_THROW(parser.extract_unsigned_bits(9), std::out_of_range);
  EXPECT_EQ(parser.extract_unsigned_bits(8), 204U);
}

// --------- TEST: .bits_remaining ---------
// ----------------------------------------

TEST(ByteParserBitsRemainingTest, BitsRemaining1) {
  uint8_t data[] = {0b10110101, 0b01100011};
  ByteParser parser(data, sizeof(data), ByteOrder::BIG_ENDIAN_ORDER);

  EXPECT_EQ(parser.extract_unsigned_bits(4), 11U);
  EXPECT_EQ(parser.extract_unsigned_bits(5), 10U);
  EXPECT_EQ(parser.bits_remaining(), 7);
  EXPECT_EQ(parser.extract_unsigned_bits(7), 99U);
}

TEST(ByteParserBitsRemainingTest, BitsRemaining2) {
  uint8_t data[] = {0b11110001};
  ByteParser parser(data, sizeof(data), ByteOrder::BIG_ENDIAN_ORDER);

  EXPECT_EQ(parser.bits_remaining(), 8);
  EXPECT_EQ(parser.extract_unsigned_bits(8), 241U);
}

TEST(ByteParserBitsRemainingTest, BitsRemaining3) {
  uint8_t data[] = {0b11110001, 0b11011101};
  ByteParser parser(data, sizeof(data), ByteOrder::BIG_ENDIAN_ORDER);

  EXPECT_EQ(parser.bits_remaining(), 16);
  EXPECT_EQ(parser.extract_unsigned_bits(16), 61917U);
}

TEST(ByteParserBitsRemainingTest, BitsAllZero2) {
  uint8_t data[] = {0b00000000, 0b00000000};
  ByteParser parser(data, sizeof(data), ByteOrder::BIG_ENDIAN_ORDER);

  EXPECT_EQ(parser.extract_unsigned_bits(2), 0U);
  EXPECT_EQ(parser.bits_remaining(), 14);
  EXPECT_EQ(parser.extract_unsigned_bits(14), 0U);
}

TEST(ByteParserBitsRemainingTest, BitsAllZero3) {
  uint8_t data[] = {0b00000000};
  ByteParser parser(data, sizeof(data), ByteOrder::BIG_ENDIAN_ORDER);

  EXPECT_EQ(parser.bits_remaining(), 8);
  EXPECT_EQ(parser.extract_unsigned_bits(8), 0U);
}

TEST(ByteParserBitsRemainingTest, BitsRemainingNull) {
  uint8_t data[] = {};
  ByteParser parser(data, sizeof(data), ByteOrder::BIG_ENDIAN_ORDER);

  EXPECT_EQ(parser.bits_remaining(), 0);
}

// --------- TEST: .extract_signed_bits ---------
// ---------------------------------------------

TEST(ByteParserExtractSBitsTest, ExtractSignedBitsPositive) {
  uint8_t data[] = {0b00000001, 0b01111111};
  ByteParser parser(data, sizeof(data), ByteOrder::BIG_ENDIAN_ORDER);

  EXPECT_EQ(parser.extract_signed_bits(8), 1);
  EXPECT_EQ(parser.extract_signed_bits(8), 127);
}

TEST(ByteParserExtractSBitsTest, ExtractSignedBitsNegative) {
  uint8_t data[] = {0b11111111, 0b10000001};
  ByteParser parser(data, sizeof(data), ByteOrder::BIG_ENDIAN_ORDER);

  EXPECT_EQ(parser.extract_signed_bits(8), -1);
  EXPECT_EQ(parser.extract_signed_bits(8), -127);
}

TEST(ByteParserExtractSBitsTest, ExtractSignedBitsMixed) {
  uint8_t data[] = {0b11111111, 0b00000001};
  ByteParser parser(data, sizeof(data), ByteOrder::BIG_ENDIAN_ORDER);

  EXPECT_EQ(parser.extract_signed_bits(8), -1);
  EXPECT_EQ(parser.extract_signed_bits(8), 1);
}

TEST(ByteParserExtractSBitsTest, ExtractSignedBitsOutOfRange) {
  uint8_t data[] = {0b11111111};
  ByteParser parser(data, sizeof(data), ByteOrder::BIG_ENDIAN_ORDER);

  EXPECT_THROW(parser.extract_signed_bits(9), std::out_of_range);
  EXPECT_EQ(parser.extract_signed_bits(8), -1);
}

// --------- TEST: .extract_string ---------
// -----------------------------------------

TEST(ByteParserExtractStringTest, ExtractStringBasic) {
  uint8_t data[] = {'H', 'e', 'l', 'l', 'o'};
  ByteParser parser(data, sizeof(data), ByteOrder::BIG_ENDIAN_ORDER);

  EXPECT_EQ(parser.extract_string(5), "Hello");
}

TEST(ByteParserExtractStringTest, ExtractStringPartial) {
  uint8_t data[] = {'H', 'e', 'l', 'l', 'o'};
  ByteParser parser(data, sizeof(data), ByteOrder::BIG_ENDIAN_ORDER);

  EXPECT_EQ(parser.extract_string(2), "He");
  EXPECT_EQ(parser.extract_string(3), "llo");
}

TEST(ByteParserExtractStringTest, ExtractStringEmpty) {
  uint8_t data[] = {};
  ByteParser parser(data, sizeof(data), ByteOrder::BIG_ENDIAN_ORDER);

  EXPECT_EQ(parser.extract_string(0), "");
}

TEST(ByteParserExtractStringTest, ExtractStringOutOfRange) {
  uint8_t data[] = {'H', 'e', 'l', 'l', 'o'};
  ByteParser parser(data, sizeof(data), ByteOrder::BIG_ENDIAN_ORDER);

  EXPECT_THROW(parser.extract_string(6), std::out_of_range);
}

// --------- TEST: .extract_unsigned_bits (LITTLE ENDIAN) ---------
// ----------------------------------------------------------------

TEST(ByteParserExtractUBitsTest, ExtractBitsLittle1) {
  uint8_t data[] = {0b11001100};
  ByteParser parser(data, sizeof(data), ByteOrder::LITTLE_ENDIAN_ORDER);
  EXPECT_EQ(parser.extract_unsigned_bits(8), 204U);
}

TEST(ByteParserExtractUBitsTest, ExtractBitsLittle2) {
  uint8_t data[] = {0b11111111};
  ByteParser parser(data, sizeof(data), ByteOrder::LITTLE_ENDIAN_ORDER);
  EXPECT_EQ(parser.extract_unsigned_bits(8), 255U);
}

TEST(ByteParserExtractUBitsTest, ExtractBitsLittleShort) {
  uint8_t data[] = {0b11001100, 0b10101010};
  ByteParser parser(data, sizeof(data), ByteOrder::LITTLE_ENDIAN_ORDER);
  EXPECT_EQ(parser.extract_unsigned_bits(16), 43724U);  // 0b1010101011001100
}