# coding: utf-8

default_config = {
    'config': {
        'sampler': {
            'type': 'const',
            'param': 1,
        },
        'logging': True,
    },
    'service_name': 'odoo'
}


def save_config(config):
    '''Saves given config dictionary to ~/.config/jaeger.yaml'''

    assert 'config' in config.keys()
    assert 'sampler' in config['config'].keys()
    assert 'type' in config['config']['sampler'].keys()
    assert 'param' in config['config']['sampler'].keys()
    assert 'logging' in config['config'].keys()

    from os import path, mkdir
    import yaml

    config_dir = path.expanduser('~/.config')
    config_yaml_path = path.join(config_dir, 'jaeger.yaml')

    if not path.isdir(config_dir):
        mkdir(config_dir)

    with open(config_yaml_path, 'w') as yaml_file:
        yaml_file.write(yaml.dump(config))


def load_config():
    '''Tries to load config yaml, returns defaults if not found'''

    from os import path
    import yaml
    from .utils import default_config, save_config

    config_dir = path.expanduser('~/.config')
    config_yaml_path = path.join(config_dir, 'jaeger.yaml')
    if path.isfile(config_yaml_path):
        with open(config_yaml_path, 'r') as yaml_file:
            try:
                config = yaml.safe_load(yaml_file)
                assert 'config' in config.keys()
                assert 'sampler' in config['config'].keys()
                assert 'type' in config['config']['sampler'].keys()
                assert 'param' in config['config']['sampler'].keys()
                assert 'logging' in config['config'].keys()
            except Exception:
                config = default_config
    else:
        save_config(default_config)
        config = default_config

    if 'service_name' in config.keys():
        service_name = config.get('service_name')
    else:
        service_name = default_config.get('service_name')

    return config['config'], service_name


def init_tracer():
    '''Initializes the global tracer object'''

    # Logging is already initialized during odoo bootup
    # import logging
    # logging.getLogger('').handlers = []
    # logging.basicConfig(format='%(message)s', level=logging.DEBUG)

    # Load config
    from .utils import load_config
    config, service_name = load_config()

    # Instatiate jaeger config object
    from jaeger_client import Config
    jaeger_config = Config(
        config=config,
        service_name=service_name,
        validate=True)

    return jaeger_config.initialize_tracer()
