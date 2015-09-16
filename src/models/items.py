import xml.etree.ElementTree as ET
import mongoengine as me

class Item(me.DynamicDocument):
	"""Represents a ROTMG item"""
	key = me.StringField(
        primary_key = True,
        required = True,
        unique = True
    )
	def from_xml(self, element):
		self.key = element.get("id").lower().replace(" ","_")
		self.name = element.get("id")
		self.type = element.get("type")
		self.attrs = dict()
		for i in element.getchildren():
			if not i.getchildren():
				self.attrs[i.tag] = (i.text, dict(i.items()))
			else:
				self.attrs[i.tag] = dict()
				for j in i.getchildren():
					self.attrs[i.tag][j.tag] = (j.text, dict(j.items()))
		return self

def from_xml():
	items = [Item().from_xml(i) for i in ET.parse("data/items.xml").getroot()]
	for i in items:
		i.save()