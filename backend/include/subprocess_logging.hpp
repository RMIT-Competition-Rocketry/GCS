#pragma once
#include <iostream>
#include <string>

namespace slogger
{

    // Make sure to flush output.
    inline void _log(const std::string &message, const std::string &level)
    {
        std::cout << "<" << level << ">:" << message << std::endl;
    }

    inline void debug(const std::string &message)
    {
        _log(message, "DEBUG");
    }

    inline void info(const std::string &message)
    {
        _log(message, "INFO");
    }

    inline void success(const std::string &message)
    {
        _log(message, "SUCCESS");
    }

    inline void warning(const std::string &message)
    {
        _log(message, "WARNING");
    }

    inline void error(const std::string &message)
    {
        _log(message, "ERROR");
    }

    inline void critical(const std::string &message)
    {
        _log(message, "CRITICAL");
    }

} // namespace slogger
