from ryu.app import d_lldp_13

from webob import Response

from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls

from ryu.app.wsgi import ControllerBase, WSGIApplication, route

from ryu.ofproto import ofproto_v1_3

from ryu.lib import dpid as dpid_lib
from ryu.lib.ofctl_utils import str_to_int

import subprocess
import re
import peewee
import networkx as nx

class SwitchController(ControllerBase):

 OpenFlowController(self, *args, **kwargs)

    def route_keisan_a(self, req, **kwargs):
        cmd = "netperf -f M -H ip | head -5 | tail -6 | awk '{ print $4 }'"

        mac_1 = cmd
    def route_keisan_b(self, req, **kwargs):
        cmd = "netperf -f M -H ip | head -5 | tail -6 | awk '{ print $4 }'"

        mac_2 = cmd

    def add_flow(self, req, **kwargs):
        if mac_1 > mac_2:
           match = parser.OFPMatch(eth_src="00:00:00:00:00:01")
           actions = [parser.OFPActionSetField(eth_dst = "00:00:00:00:00:02")]
        else:
           match = parser.OFPMatch(eth_src="00:00:00:00:00:01")
           actions = [parser.OFPActionSetField(eth_dst = "00:00:00:00:00:03")]
