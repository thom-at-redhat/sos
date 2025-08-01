# Copyright (C) 2021 Nadia Pinaeva <npinaeva@redhat.com>
# This file is part of the sos project: https://github.com/sosreport/sos
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# version 2 of the GNU General Public License.
#
# See the LICENSE file in the source distribution for further information.

import glob
from sos.report.plugins import Plugin, RedHatPlugin


class OpenshiftOVN(Plugin, RedHatPlugin):
    """This plugin is used to collect OCP 4.x OVN logs.
    """
    short_desc = 'Openshift OVN'
    plugin_name = "openshift_ovn"
    containers = ('ovnkube-master', 'ovnkube-node', 'ovn-ipsec',
                  'ovnkube-controller')
    profiles = ('openshift',)

    def setup(self):

        all_logs = self.get_option("all_logs")

        self.add_copy_spec([
            "/var/lib/ovn/etc/ovnnb_db.db",
            "/var/lib/ovn/etc/ovnsb_db.db",
            "/var/lib/openvswitch/etc/keys"
        ], sizelimit=300)

        # Collect ovn interconnect specific db files if exists.
        self.add_copy_spec([
            "/var/lib/ovn-ic/etc/ovnnb_db.db",
            "/var/lib/ovn-ic/etc/ovnsb_db.db"
        ], sizelimit=300)

        # Collect libovsdb logs in case of ovn interconnect setup.
        if not all_logs:
            self.add_copy_spec([
                "/var/lib/ovn-ic/etc/libovsdb.log",
                "/var/lib/ovn-ic/etc/libovsdb*log.gz"
            ], sizelimit=100)
        else:
            self.add_copy_spec("/var/lib/ovn-ic/etc/libovsdb*log*")

        # The ovn cluster/status is not valid anymore for interconnect setup.
        self.add_cmd_output([
            'ovn-appctl -t /var/run/ovn/ovnnb_db.ctl ' +
            'cluster/status OVN_Northbound',
            'ovn-appctl -t /var/run/ovn/ovnsb_db.ctl ' +
            'cluster/status OVN_Southbound'],
            container='ovnkube-master',
            runtime='crio')
        # We need to determine the actual file name to send
        # to the command
        files = glob.glob("/var/run/ovn/ovn-controller.*.ctl")
        for file in files:
            self.add_cmd_output([
                f"ovs-appctl -t {file} ct-zone-list"],
                container='ovnkube-node',
                runtime='crio')
            self.add_cmd_output([
                f"ovs-appctl -t {file} ct-zone-list"],
                container='ovnkube-controller',
                runtime='crio')
        # Collect ovs ct-zone-list directly on host for interconnect setup.
        files = glob.glob("/var/run/ovn-ic/ovn-controller.*.ctl")
        for file in files:
            self.add_cmd_output([
                f"ovs-appctl -t {file} ct-zone-list'"],
                runtime='crio')
        self.add_cmd_output([
            'ovs-appctl -t ovs-monitor-ipsec tunnels/show',
            'ipsec status',
            'certutil -L -d sql:/etc/ipsec.d'],
            container='ovn-ipsec',
            runtime='crio')
