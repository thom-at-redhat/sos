# This file is part of the sos project: https://github.com/sosreport/sos
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# version 2 of the GNU General Public License.
#
# See the LICENSE file in the source distribution for further information.

# This plugin enables collection of logs for Power systems

import re
from sos.report.plugins import Plugin, IndependentPlugin, SoSPredicate


class IprConfig(Plugin, IndependentPlugin):

    short_desc = 'IBM Power RAID storage adapter configuration information'

    plugin_name = 'iprconfig'
    packages = ('iprutils',)
    architectures = ('ppc64.*',)

    def setup(self):

        show_ioas = self.collect_cmd_output(
                "iprconfig -c show-ioas",
                pred=SoSPredicate(self, kmods=['sg'])
        )
        if not show_ioas['status'] == 0:
            return

        self.add_cmd_output([
            "iprconfig -c show-config",
            "iprconfig -c show-alt-config",
            "iprconfig -c show-arrays",
            "iprconfig -c show-jbod-disks",
            "iprconfig -c show-ioas",
            "iprconfig -c show-hot-spares",
            "iprconfig -c show-af-disks",
            "iprconfig -c show-all-af-disks",
            "iprconfig -c show-slots",
            "iprconfig -c dump"
        ])

        devices = []
        if show_ioas['output']:
            dev = re.compile('sg')
            for line in show_ioas['output'].splitlines():
                temp = line.split(' ')
                # temp[0] holds the device name
                if dev.search(temp[0]):
                    devices.append(temp[0])

        for device in devices:
            self.add_cmd_output(f"iprconfig -c show-details {device}")
            self.add_cmd_output(f"iprconfig -c show-battery-info {device}")
            self.add_cmd_output(f"iprconfig -c show-perf {device}")

        # Look for IBM Power RAID enclosures (iprconfig lists them)
        show_config = self.collect_cmd_output("iprconfig -c show-config")
        if not show_config['status'] == 0:
            return

        if not show_config['output']:
            return

# iprconfig -c show-config
# Name   PCI/SCSI Location         Description               Status
# ------ ------------------------- ------------------------- -----------------
#        0005:60:00.0/0:            PCI-E SAS RAID Adapter    Operational
# sda    0005:60:00.0/0:0:0:0       Physical Disk             Active
# sdb    0005:60:00.0/0:1:0:0       Physical Disk             Active
# sdc    0005:60:00.0/0:2:0:0       Physical Disk             Active
# sdd    0005:60:00.0/0:3:0:0       Physical Disk             Active
# sde    0005:60:00.0/0:4:0:0       Physical Disk             Active
# sdf    0005:60:00.0/0:5:0:0       Physical Disk             Active
#        0005:60:00.0/0:8:0:0       Enclosure                 Active
#        0005:60:00.0/0:8:1:0       Enclosure                 Active

        show_alt_config = "iprconfig -c show-alt-config"
        altconfig = self.collect_cmd_output(show_alt_config)
        if (altconfig['status'] != 0) or not altconfig['output']:
            return

# iprconfig -c show-alt-config
# Name   Resource Path/Address      Vendor   Product ID       Status
# ------ -------------------------- -------- ---------------- -----------------
# sg9    0:                         IBM      57C7001SISIOA    Operational
# sg0    0:0:0:0                    IBM      MBF2300RC        Active
# sg1    0:1:0:0                    IBM      MBF2300RC        Active
# sg2    0:2:0:0                    IBM      HUC106030CSS600  Active
# sg3    0:3:0:0                    IBM      HUC106030CSS600  Active
# sg4    0:4:0:0                    IBM      HUC106030CSS600  Active
# sg5    0:5:0:0                    IBM      HUC106030CSS600  Active
# sg7    0:8:0:0                    IBM      VSBPD6E4A  3GSAS Active
# sg8    0:8:1:0                    IBM      VSBPD6E4B  3GSAS Active

        for line in show_config['output'].splitlines():
            if "Enclosure" in line:
                temp = re.split(r'\s+', line)
                # temp[1] holds the PCI/SCSI location
                _, scsi = temp[1].split('/')
                for alt_line in altconfig['output'].splitlines():
                    if scsi in alt_line:
                        temp = alt_line.split(' ')
                        # temp[0] holds device name
                        self.add_cmd_output("iprconfig -c "
                                            f"query-ses-mode {temp[0]}")

# vim: set et ts=4 sw=4 :
