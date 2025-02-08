
# Development notes

## Device Emulation 

Example output from `socat` at startup. This shows what the device names are

```terminal
2025/02/06 20:53:44 socat[56067] N PTY is /dev/ttys012
2025/02/06 20:53:44 socat[56067] N PTY is /dev/ttys01
```

And when you write to them

```terminal
$ echo "Hello Serial" > /dev/ttys012
$ echo "Hello Serial" > /dev/ttys01
```
```terminal
2025/02/06 21:08:47 socat[56254] N write(7, 0x126814000, 13) completed
2025/02/06 21:08:53 socat[56254] N write(7, 0x126814000, 13) complete
```

Please note that both fake serial devices are linked, but when you read from one the buffer is cleared. That means that you use one as the 'fake device' and the other can just be for montitoring because nothing will steal the bytes going to it from the other linked device

---

[Home](../README.md)