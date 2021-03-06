
import os
from pyiem.network import Table as NetworkTable
import pg
mesosite = pg.connect('mesosite', 'iemdb')
import glob

nt = NetworkTable('IA_RWIS')


def find_id(rid):
    for sid in nt.sts.keys():
        if rid == nt.sts[sid]['remote_id']:
            return sid
    return None

os.chdir("/mesonet/data/dotcams")
files = glob.glob("*640x480.jpg")
for fn in files:
    cid = fn[:11]

    rs = mesosite.query("SELECT * from webcams WHERE id = '%s'" % (cid,
                                                            )).dictresult()
    if len(rs) > 0:
        continue

    rid = cid[6:8]
    nwsli = find_id(int(rid))
    if nwsli is None:
        print 'Failed to find remote_id: %s' % (rid,)
        continue

    rs = mesosite.query("""SELECT name, ST_x(geom) as lon, ST_y(geom) as lat
    from stations where id = '%s'""" % (nwsli,)).dictresult()
    lon = rs[0]['lon']
    lat = rs[0]['lat']
    name = rs[0]['name']
    print 'Adding %s name [%s] lon [%s] lat [%s]' % (cid, name, lon, lat)
    sql = """insert into webcams (sts, id, name, pan0, online, network,
         geom, removed, state) values (now(), '%s', '%s', 0, 't',
         'IDOT', 'SRID=4326;POINT(%s %s)', 'f', 'IA')""" % (cid, name, lon,
                                                            lat)
    mesosite.query(sql)
