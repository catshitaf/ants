__author__ = 'wcong'
import json
from ants import manager
import multicast
import transport
from ants.webservice import webservice
from ants.cluster import cluster
from ants.crawl import crawl
import nodeinfo
import rpc
import pickle
from ants.utils import jsonextends
import logging


'''
what a node would do
init multicast
init transport
init web service
open spider

accept request and deal with it
'''


class NodeManager(manager.Manager):
    def __init__(self, settings):
        self.settings = settings
        self.node_info = nodeinfo.NodeInfo(multicast.get_host_name(), self.settings.get('TRANSPORT_PORT'))
        self.cluster_manager = cluster.ClusterManager(self)
        self.transport_manager = transport.TransportManager(self)
        self.multicast_manager = multicast.MulticastManager(self, self.cluster_manager.find_node)
        self.webservice_manager = webservice.WebServiceManager(self)

        # net work manager should start first
        self.manager_list = [
            self.transport_manager,
            self.multicast_manager,
            self.cluster_manager,
            self.webservice_manager]

        self.crawl_client = crawl.CrawlClient(self)


    def stop(self):
        for inner_manager in self.manager_list:
            inner_manager.stop()


    def start(self):
        '''
        we start all the manager
        find node
        and ready to start
        :return:
        '''
        logging.info('start to init manager')
        for inner_manager in self.manager_list:
            inner_manager.start()

    def connect_to_node(self, ip, port):
        if ip == self.node_info.ip and port == self.node_info.port:
            return
        self.transport_manager.run_client(ip, port)

    def add_node_to_cluster(self, ip, port):
        self.cluster_manager.add_node(ip, port)

    def is_idle(self, spider_name, node=None):
        if not node or node == self.node_info:
            if self.crawl_client.is_idle(spider_name):
                self.idle_engine_manager(spider_name, self.node_info.ip, self.node_info.port)
        else:
            self.transport_manager.send_request(node.ip, node.port, rpc.REQUEST_INIT_ENGINE + spider_name)

    def idle_engine_manager(self, spider_name, ip, port):
        self.cluster_manager.idle_engine_manager(spider_name, nodeinfo.NodeInfo(ip, port))

    def init_engine(self, spider_name, node=None):
        if not node or node == self.node_info:
            self.crawl_client.init_engine(spider_name)
            if self.node_info == self.cluster_manager.cluster_info.master_node:
                self.init_engine_manager(spider_name, self.node_info.ip, self.node_info.port)
        else:
            self.transport_manager.send_request(node.ip, node.port, rpc.REQUEST_INIT_ENGINE + spider_name)

    def init_engine_manager(self, spider_name, ip, port):
        self.cluster_manager.init_engine_manager(spider_name, nodeinfo.NodeInfo(ip, port))

    def send_request_to_client(self, request, node=None):
        if not node or node == self.node_info:
            self.crawl_client.accept_request(request.spider_name, request)
        else:
            self.transport_manager.send_request(node.ip, node.port,
                                                rpc.REQUEST_SEND_REQUEST + pickle.dumps(request))

    def send_request_to_master(self, request):
        master_node = self.cluster_manager.cluster_info.master_node
        if master_node == self.node_info:
            self.cluster_manager.add_request(request)
        else:
            self.transport_manager.send_request(master_node.ip, master_node.port,
                                                rpc.RESPONSE_SEND_REQUEST + pickle.dumps(request))


    def start_a_engine(self, spider_name):
        master_node = self.cluster_manager.cluster_info.master_node
        if self.node_info == master_node:
            self.cluster_manager.start_a_engine(spider_name)
        else:
            self.transport_manager.send_request(master_node.ip, master_node.port,
                                                rpc.REQUEST_START_A_ENGINE + spider_name)



