import argparse
import logging
import os
import sys
import dns.resolver

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# append project dir to python path
from labchain.blockchainNode import BlockChainNode  # noqa
from labchain.dashboardDB import DashBoardDB
from labchain.configReader import ConfigReader  # noqa
from labchain.utility import Utility  # noqa
from labchain import event  # noqa
from labchain.event import EventBus  # noqa
from labchain.plot import BlockchainPlotter  # noqa

# set TERM environment variable if not set
if 'TERM' not in os.environ:
    os.environ['TERM'] = 'xterm-color'

CONFIG_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir,
                                           'labchain', 'resources',
                                           'node_configuration.ini'))
CONFIG_DIRECTORY = os.path.join(os.path.expanduser("~"), '.labchain')
DEFAULT_PLOT_DIRECTORY = os.path.join(CONFIG_DIRECTORY, 'plot')


def create_node(node_port, peer_list, plot_dir=None):
    event_bus = EventBus()
    if plot_dir:
        plotter = BlockchainPlotter(plot_dir)
        event_bus.register(event.EVENT_BLOCKCHAIN_INITIALIZED, plotter.plot_blockchain)
        event_bus.register(event.EVENT_BLOCK_ADDED, plotter.plot_blockchain)
        event_bus.register(event.EVENT_BLOCK_ADDED, plotter.generate_block_detail_page)
    return BlockChainNode(CONFIG_FILE, event_bus, node_port, peer_list)


def setup_logging(verbose, very_verbose):
    if very_verbose:
        logging.basicConfig(level=logging.DEBUG)
    elif verbose:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


def parse_args():
    parser = argparse.ArgumentParser(description='CLI node for Labchain.')
    parser.add_argument('--port', default=8080, help='The port address of the Labchain node')
    parser.add_argument('--peers', nargs='*', default=[], help='The peer list address of the Labchain node')
    parser.add_argument('--verbose', '-v', action='store_true')
    parser.add_argument('--very-verbose', '-vv', action='store_true')
    parser.add_argument('--plot', '-p', action='store_true')
    parser.add_argument('--plot-dir', default=DEFAULT_PLOT_DIRECTORY,
                        help='Enable plotting graphics to the specified dir')
    return parser.parse_args()


def parse_peers(peer_args):
    result = {}
    try:
        config = ConfigReader(CONFIG_FILE)
        seed_domain = config.get_config(section="NETWORK", option="DNS_SEED_DOMAIN")
        resolver = config.get_config(section="NETWORK", option="DNS_CLIENT")
        default_port = config.get_config(section="NETWORK", option="PORT", fallback=8080)
        myResolver = dns.resolver.Resolver(configure=False)
        myResolver.nameservers = [resolver]
        myResolver.lifetime = 2
        answers = myResolver.query(seed_domain, "A")
        for a in answers.rrset.items:
            host_addr = a.to_text()
            logging.info("Adding Node peer IP {} received using DNS SEED peer discovery ... ".format(host_addr))
            if host_addr not in result:
                result[host_addr] = {}
            result[host_addr][default_port] = {}
    except Exception as e:
        logging.error(str(e))

    for peer_str in peer_args:
        host, port = peer_str.split(':')
        if host not in result:
            result[host] = {}
        result[host][port] = {}
    return result


if __name__ == '__main__':
    test = sys.argv
    args = parse_args()
    setup_logging(args.verbose, args.very_verbose)
    initial_peers = parse_peers(args.peers)
    Utility.print_labchain_logo()
    if args.plot:
        plot_dir = args.plot_dir
    else:
        plot_dir = None
    DashBoardDB.instance().set_plot_dir(plot_dir)
    node = create_node(args.port, initial_peers, plot_dir)
