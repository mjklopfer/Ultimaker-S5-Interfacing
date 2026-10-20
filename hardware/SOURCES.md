# Source references and provenance

The notes separate observed configuration, host interface contracts, public
related-board references and proposed implementation. No full proprietary source,
firmware or drawing is reproduced. A link being publicly reachable does not
change the linked material's licensing or usage restrictions.

- [Manufacturer S5 R1 electronics repair reference](https://um-support-files.ultimaker.com/manuals/repair-calibration/S-series/UMS5R1%20-%20Electronics.pdf): board/connector context and repair precautions. Linked only; the document carries its own restrictions.
- [UltiMaker Marlin repository](https://github.com/Ultimaker/UltimakerMarlin): public source reference for related motion-controller interfaces. An upstream branch is not proof of the binary running on a particular printer.
- [UltiMaker kernel device-tree reference](https://github.com/Ultimaker/um-kernel/blob/master/sun7i/dts/2621-UM3XL.dts): related platform/audio configuration.
- [UltiMaker hardware repository](https://github.com/Ultimaker/Ultimaker3): older related Olimex interface drawings. They do not settle exact R1 wiring.
- [Arduino Mega pin reference](https://docs.arduino.cc/resources/pinouts/A000067-full-pinout.pdf): proposed controller allocation, not S5 stock connector numbering.
- [Noctua PWM specification](https://cdn.noctua.at/media/Noctua_PWM_specifications_white_paper.pdf): generic fan-interface guidance; exact installed fan/levels remain unknown.
- [SHT4x breakout reference](https://learn.adafruit.com/adafruit-sht40-temperature-humidity-sensor/pinouts) and [TCA9548A breakout reference](https://learn.adafruit.com/adafruit-tca9548a-1-to-8-i2c-multiplexer-breakout/pinouts): proposed sensor hardware only.

The printer also serves documentation locally at `/docs/api/` and
`/cluster-api/v1/`. Supply your own printer origin; none is bundled. The public
structural catalogs describe methods, paths, parameters and types, not an
extracted implementation. Internal Linux paths recorded beside register names
identify generic host consumers and their source locations; the files themselves
and source hashes are not included.
