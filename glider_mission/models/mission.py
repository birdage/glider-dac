import os
import urllib

from glider_mission import db
from datetime import datetime
from flask.ext.mongokit import Document
from bson.objectid import ObjectId

@db.register
class Mission(Document):
    __collection__ = 'missions'
    use_dot_notation = True
    use_schemaless = True

    structure = {
        'name'                      : unicode,
        'user_id'                   : ObjectId,
        'username'                  : unicode,  # The cached username to lightly DB load
        'mission_dir'               : unicode,
        'estimated_deploy_date'     : datetime,
        'estimated_deploy_location' : unicode,  # WKT text
        'wmo_id'                    : unicode,
        'completed'                 : bool,
        'created'                   : datetime,
        'updated'                   : datetime
    }

    default_values = {
        'created': datetime.utcnow,
        'completed': False
    }

    def save(self):
        if self.username is None or self.username == u'':
            user = db.User.find_one( { '_id' : self.user_id } )
            self.username = user.username

        self.sync()
        super(Mission, self).save()

    @property
    def dap(self):
        return u"http://tds.gliders.ioos.us/thredds/dodsC/%s_%s_Time.ncml" % (self.username, self.name)

    @property
    def sos(self):
        return u"http://tds.gliders.ioos.us/thredds/sos/%s_%s_Time.ncml" % (self.username, self.name)

    @property
    def iso(self):
        catalog_parameter = u'http://tds.gliders.ioos.us/thredds/%s/%s/catalog.html' % (self.username, self.name)
        dataset_parameter = u'%s_%s_Time' % (self.username, self.name)
        query = urllib.urlencode({ 'catalog' : catalog_parameter, 'dataset' : dataset_parameter })
        return u"http://tds.gliders.ioos.us/thredds/iso/%s_%s_Time.ncml?%s" % (self.username, self.name, query)

    def sync(self):
        if not os.path.exists(self.mission_dir):
            try:
                os.makedirs(self.mission_dir)
            except OSError:
                pass

        # Serialize Mission model to disk
        json_file = os.path.join(self.mission_dir, "mission.json")
        with open(json_file, 'w') as f:
            f.write(self.to_json())
