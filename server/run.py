import os

data = open('nginx.conf.dist', 'r').read().strip()
config = {
    'path': os.getcwd(),
}
out = data % config
open('nginx.conf', 'w').write(out)

os.system('nginx -c {path}'.format(path=os.path.join(os.getcwd(), 'nginx.conf')))
