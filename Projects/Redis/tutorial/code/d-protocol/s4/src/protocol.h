#pragma once

#include <cstdint>
#include <string>
#include <vector>
using namespace std;

// Every number on the wire is a 4-byte uint32_t, stored the way the CPU keeps
// it in memory (little-endian on x86 and ARM). See README.md for the layout.
//
// We keep raw bytes in a plain std::string: a string can hold any bytes,
// including 0, and already knows how to grow (+=) and shrink (erase).
const size_t MAX_MSG = 4096;  // biggest payload we accept
const size_t HEADER_LEN = 4;  // the length in front of every message
const int PORT = 1234;

// First byte of every response.
enum Status { RES_OK = 0, RES_ERR = 1, RES_NX = 2 };  // NX = key not found

void appendU32(string &out, uint32_t v);        // add v's 4 bytes to the end of out
uint32_t readU32(const string &s, size_t pos);  // read 4 bytes starting at s[pos]

// Request payload: [nargs] then [len][bytes] for each arg.
string encodeRequest(const vector<string> &args);
bool parseRequest(const string &payload, vector<string> &args);  // false if malformed

// Response payload: [status byte] then, only if data is non-empty, [len][bytes].
// So an empty value looks the same on the wire as "no value".
string encodeResponse(Status status, const string &data = "");
bool parseResponse(const string &payload, Status &status, string &data);

// Frame: [payload length][payload]. Every message on the socket is a frame.
string makeFrame(const string &payload);

enum FrameResult { FRAME_INCOMPLETE, FRAME_TOO_BIG, FRAME_COMPLETE };
FrameResult tryParseFrame(const string &buf, size_t &payloadLen);
