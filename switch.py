from ryu.base import app_manager

from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls

from ryu.ofproto import ofproto_v1_3
from ryu.ofproto import ether
from ryu.ofproto import inet
from ryu.lib.packet import packet
from ryu.lib.packet import ipv4
from ryu.lib.packet import vlan
from ryu.lib.packet import ethernet
import subprocess


class SwitchController(ControllerBase):

    def __init__(self, req, link, data, **config):
        super(SwitchController, self).__init__(req, link, data, **config)
        self.switch_app = data[simple_switch_instance_name]

    @route('switch', '/add/{start}/{end}', methods=['GET'])
    def add_mac_table(self, req, **kwargs):
        start = kwargs['start']
        end = kwargs['end']

        s = Visualization_vlans.get(Visualization_vlans.start == start)
        e = Visualization_vlans.get(Visualization_vlans.end == end)

        if start == s.start and end == e.end:
            self.path_division(s, e)

    @route('switch', '/del/{vlan}', methods=['GET'])
    def del_mac_table(self, req, **kwargs):
        vlan = kwargs['vlan']

        v = Visualization_vlans.get(Visualization_vlans.vlanid == vlan)
        s = v.start
        e = v.end
        port1 = s.split("-")
        port2 = e.split("-")

        self.switch_app.del_flow(vlan, port1[1], port2[1])


    @route('switch', '/modify/{start}/{end}', methods=['GET'])
    def modify_mac_table(self, req, **kwargs):
        start = kwargs['start']
        end = kwargs['end']

        s = Visualization_vlans.get(Visualization_vlans.start == start)
        e = Visualization_vlans.get(Visualization_vlans.end == end)

        port1 = start.split("-")
        port2 = end.split("-")

        self.switch_app.del_flow(s.vlanid, port1[1], port2[1])

        if start == s.start and end == e.end:
            self.path_division(s, e)

    @route('switch', '/auto/{host_name1}/{host_name2}/{vlanid}', methods=['GET'])
    def auto_mac_table(self, req, **kwargs):
        host_name1 = kwargs['host_name1']
        host_name2 = kwargs['host_name2']
        vlan = kwargs['vlanid']
        start = Visualization_topologies.get(Visualization_topologies.dport2 == host_name1)
        end = Visualization_topologies.get(Visualization_topologies.dport2 == host_name2)

        vlans = Visualization_vlans.select().where((Visualization_vlans.start == start.dport1) & (Visualization_vlans.end == end.dport1))
        if vlans.exists():
            cmd = "curl -X GET http://10.50.0.101:8080/del/" + str(vlan)

            subprocess.call(cmd, shell=True)

        route = Visualization_route.select().where((Visualization_route.start == start.dport1) & (Visualization_route.end == end.dport1))
        if route.exists():
            self.dijkstra(route[0], vlan)


    def path_division(self, start, end):
        vlan = start.vlanid
        path = start.path
        path_list = re.split('[|,]',path)
        path_join =[]
        for i in range(len(path_list)):
            if i % 2 != 0:
                path_join.append(",".join([path_list[i-1], path_list[i]]))

        path = re.split('[,-]',path_join[0])
        self.switch_app.set_push_pop_vlan_flow1(vlan, int(path[0]), int(path[1]), int(path[3]))

        path = re.split('[,-]',path_join[-1])
        self.switch_app.set_push_pop_vlan_flow2(vlan, int(path[0]), int(path[1]), int(path[3]))

        if len(path_join) != 2:
            for j in range(1, len(path_join)-1):
                path = re.split('[,-]',path_join[j])
                self.switch_app.set_vlan_flow(vlan, int(path[0]), int(path[1]), int(path[3]))

    def dijkstra(self, path, vlan):
        path = path.route
        route_list = re.split('[|,]',path)
        path_join = []
        path_route = []
        if len(route_list) != 4:
            path_route.append(route_list[1])
            Graph = nx.DiGraph()
            node1 = re.split('[-]',route_list[1])
            node2 = re.split('[-]',route_list[-2])
            Graph.add_nodes_from([route_list[0], node1[0]])
            Graph.add_edge(route_list[0], node1[0], weight=1)
            Graph.add_nodes_from([node2[0],route_list[-1]])
            Graph.add_edge(node2[0], route_list[-1], weight=1)

            for i in range(2,len(route_list)-2):
                if i % 2 != 0:
                    path_join.append(",".join([route_list[i-1], route_list[i]]))

            for i in range(len(path_join)):
                node_edge = re.split('[-,]',path_join[i])
                Graph.add_nodes_from([node_edge[0], node_edge[2]])
                if node1[0] == node_edge[0]:
                    Graph.add_edge(node_edge[0], node_edge[2], weight=1+1)
                else:
                    Graph.add_edge(node_edge[2], node_edge[0], weight=2+i)

            route_path = nx.dijkstra_path(Graph, source=route_list[0], target=route_list[-1])

            for i in range(len(path_join)):
                node_edge = re.split('[-,]',path_join[i])
                for j in range(len(route_path)-1):
                    if (node_edge[0] == route_path[j] and node_edge[2] == route_path[j+1]) or (node_edge[0] == route_path[j+1] and node_edge[2] == route_path[j]):
                        path_route.append(path_join[i])

            path_route.append(route_list[-2])
            path = "|".join(path_route)
            path_length = re.split('[|,]',path)
            path_length.remove(path_length[0])
            path_length.remove(path_length[-1])

            vlans = Visualization_vlans.select().where((Visualization_vlans.start == route_list[1]) & (Visualization_vlans.end == route_list[-2]))
            if vlans.exists():
                vlans = Visualization_vlans.update(path=path,path_length = len(path_length)).where((Visualization_vlans.start == route_list[1]) & (Visualization_vlans.end == route_list[-2]))
                vlans.execute()

                cmd = "curl -X GET http://10.50.0.101:8080/add/" + route_list[1] + "/" + route_list[-2]


                subprocess.call(cmd, shell=True)
            else:
                vlans = Visualization_vlans.insert(vlanid=vlan,start=route_list[1], end=route_list[-2], path=path, path_length = len(path_length))
                vlans.execute()

                cmd = "curl -X GET http://10.50.0.101:8080/add/" + route_list[1] +  "/"  +route_list[-2]

                subprocess.call(cmd, shell=True)

        else:
            vlans = Visualization_vlans.select().where((Visualization_vlans.start == route_list[1]) & (Visualization_vlans.end == route_list[-2]))
            if vlans.exists():
                path = "|".join([route_list[1],route_list[-2]])
                vlans = Visualization_vlans.update(path=path, path_length = len(path_length)).where((Visualization_vlans.start == route_list[1]) & (Visualization_vlans.end == route_list[-2]))
                vlans.execute()

                cmd = "curl -X GET http://10.50.0.101:8080/add/" + route_list[1] + "/" + route_list[-2]

                subprocess.call(cmd, shell=True)
            else:
                path = "|".join([route_list[1],route_list[-2]])
                vlans = Visualization_vlans.insert(vlanid=vlan,start=route_list[1], end=route_list[-2], path=path, path_length = len(path_length))
                vlans.execute()

                cmd = "curl -X GET http://10.50.0.101:8080/add/" + route_list[1] + "/" + route_list[-2]

                subprocess.call(cmd, shell=True)

    @route('switch', '/benchmark', methods=['GET'])
    def benchmark(self, req, **kwargs)def auto_mac_table(self, req, **kwargs):
        host_name1 = kwargs['host_name1']
        host_name2 = kwargs['host_name2']
        vlan = kwargs['vlanid']
        start = Visualization_topologies.get(Visualization_topologies.dport2 == host_name1)
        end = Visualization_topologies.get(Visualization_topologies.dport2 == host_name2)

        vlans = Visualization_vlans.select().where((Visualization_vlans.start == start.dport1) & (Visualization_vlans.end == end.dport1))
        if vlans.exists():
            cmd = "curl -X GET http://10.50.0.101:8080/del/" + str(vlan)

            subprocess.call(cmd, shell=True)

        route = Visualization_route.select().where((Visualization_route.start == start.dport1) & (Visualization_route.end == end.dport1))
        if route.exists():
            self.dijkstra(route[0], vlan)


    def path_division(self, start, end):
        vlan = start.vlanid
        path = start.path
        path_list = re.split('[|,]',path)
        path_join =[]
        for i in range(len(path_list)):
            if i % 2 != 0:
                path_join.append(",".join([path_list[i-1], path_list[i]]))

        path = re.split('[,-]',path_join[0])
        self.switch_app.set_push_pop_vlan_flow1(vlan, int(path[0]), int(path[1]), int(path[3]))

        path = re.split('[,-]',path_join[-1])
        self.switch_app.set_push_pop_vlan_flow2(vlan, int(path[0]), int(path[1]), int(path[3]))

        if len(path_join) != 2:
            for j in range(1, len(path_join)-1):
                path = re.split('[,-]',path_join[j])
                self.switch_app.set_vlan_flow(vlan, int(path[0]), int(path[1]), int(path[3])):
