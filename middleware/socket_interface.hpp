#ifndef SOCKET_INTERFACE_HPP
#define SOCKET_INTERFACE_HPP

class Interface
{
public:
    // Pure virtual function
    virtual void draw() const = 0;

    // Virtual destructor (best practice for polymorphic base classes)
    virtual ~Interface() {}
};

#endif
// SOCKET_INTERFACE_HPP