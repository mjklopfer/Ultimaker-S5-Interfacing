# Source references and provenance

The notes separate observed configuration, host interface contracts, public
related-board references and proposed implementation. No full proprietary source,
firmware or drawing is reproduced. A link being publicly reachable does not
change the linked material's licensing or usage restrictions.

- [Manufacturer S5 R1 electronics repair reference](https://um-support-files.ultimaker.com/manuals/repair-calibration/S-series/UMS5R1%20-%20Electronics.pdf): board/connector context and repair precautions. Linked only; the document carries its own restrictions.
- [MakerPoint UMB cable L200 (MS)](https://www.makerpoint.nl/en-gb/3d-printing/accessories/parts_all/ultimaker-umb-cable-l200-ms-210000004246): retailer lists manufacturer part 80-214855, 200 mm, for Material Station connection, compatible with S5 R1/R2. The photo shows right-angle circular multi-pin ends; exact connector standard/contact count and electrical pinout are not established. Air Manager compatibility is listed as No; this does not establish a different electrical protocol.
- [UltiMaker Marlin repository](https://github.com/Ultimaker/UltimakerMarlin): public source reference for related motion-controller interfaces. An upstream branch is not proof of the binary running on a particular printer.
- [Print-core overview](https://support.ultimaker.com/articles/Knowledge/000002903) and [S-series core exchange](https://support.ultimaker.com/articles/Knowledge/1667411590923): EEPROM identity and automatic detection; see [miscellaneous notes](MISC_NOTES.md) for upstream service-command limits.
- [Ultimainboard v2.1.4 community announcement](https://community.ultimaker.com/topic/21733-ultimainboard-v214-some-documentation-schematics-pinout-dimensions-step-3d-bom/) and [official UM2 board directory](https://github.com/Ultimaker/Ultimaker2/tree/master/1546%20ultimainboard%20V2.1.4): older Ultimaker 2 design references, not the S5 R1 schematic or proof of its UMB pinout.
- [UltiMaker kernel device-tree reference](https://github.com/Ultimaker/um-kernel/blob/master/sun7i/dts/2621-UM3XL.dts): related platform/audio configuration.
- [UltiMaker hardware repository](https://github.com/Ultimaker/Ultimaker3): older related Olimex interface drawings. They do not settle exact R1 wiring.
- [ST NUCLEO-F072RB](https://www.st.com/en/evaluation-tools/nucleo-f072rb.html) and [NUCLEO-F303ZE](https://www.st.com/en/evaluation-tools/nucleo-f303ze.html): suggested separate Air/Material STM32 bench boards; S5 compatibility remains untested.
- [STM32duino APIs](https://github.com/stm32duino/Arduino_Core_STM32/wiki/API) and [ST AN3155](https://www.st.com/resource/en/application_note/an3155-how-to-use-usart-protocol-in-bootloader-on-stm32-mcus-stmicroelectronics.pdf): framework and standard bootloader references, distinct from S5 chain-control extensions.
- [Noctua PWM specification](https://cdn.noctua.at/media/Noctua_PWM_specifications_white_paper.pdf): generic fan-interface guidance; exact installed fan/levels remain unknown.
- [Air Manager / SMB pinout discussion](https://community.ultimaker.com/topic/39588-air-manager-andor-smb-pinout/): dated user report about feed-forward chamber behavior; no verified pinout or electrical/protocol identification is supplied. See [miscellaneous notes](MISC_NOTES.md).
- [SHT4x breakout reference](https://learn.adafruit.com/adafruit-sht40-temperature-humidity-sensor/pinouts) and [TCA9548A breakout reference](https://learn.adafruit.com/adafruit-tca9548a-1-to-8-i2c-multiplexer-breakout/pinouts): proposed sensor hardware only.

The printer also serves documentation locally at `/docs/api/` and
`/cluster-api/v1/`. Supply your own printer origin; none is bundled. The public
structural catalogs describe methods, paths, parameters and types, not an
extracted implementation. Internal Linux paths recorded beside register names
identify generic host consumers and their source locations; the files themselves
and source hashes are not included.
