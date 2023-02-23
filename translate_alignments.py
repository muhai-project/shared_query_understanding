# This script translates the provided alignments of the datasets in OWL terms, depending on whether they are property or class alignments.
import xml.etree.ElementTree as ET
from rdflib import Graph, URIRef, RDF, OWL
import os

original_ontologies_dir = "data_preparation/oa4qa_bundle/data/original"
reference_alignments_dir = "data_preparation/oa4qa_bundle/data/reference"

owl_alignments_dir = "dataset/reference_alignments_owl"

if not os.path.isdir(owl_alignments_dir):
	os.makedirs(owl_alignments_dir)

prefixes = ["cmt", "conference", "confof", "edas", "ekaw", "iasted", "sigkdd"]

# read the ontologies
ontologies = {}
for prefix in prefixes:
	ontologies[prefix] = Graph()
	ontologies[prefix].parse(original_ontologies_dir + "/" + prefix + ".owl")

# read the alignments
prefix_pairs = ["cmt-conference", "cmt-confof", "cmt-edas", "cmt-ekaw", "cmt-iasted",
			 "cmt-sigkdd", "conference-confof", "conference-edas", "conference-ekaw",
			 "conference-iasted", "conference-sigkdd", "confof-edas", "confof-ekaw",
			 "confof-iasted", "confof-sigkdd", "edas-ekaw", "edas-iasted", "edas-sigkdd",
			 "ekaw-iasted", "ekaw-sigkdd", "iasted-sigkdd"]

alignments = {}

for prefix_pair in prefix_pairs:

	ont1 = prefix_pair.split("-")[0]
	ont2 = prefix_pair.split("-")[1]

	alignments[prefix_pair] = Graph()

	root = ET.parse(reference_alignments_dir + "/" + prefix_pair + ".rdf").getroot()

	for i in range(len(root[0]) - 5):
		alignment = root[0][5 + i]

		aligned_entity_a = URIRef(list(alignment[0][0].attrib.values())[0])
		aligned_entity_b = URIRef(list(alignment[0][1].attrib.values())[0])


		# retrieve the type of one of the entities, form its original ontology
		entity_type = list(ontologies[ont1].objects(aligned_entity_a, RDF.type))[0]

		# in case of class alignment
		if (aligned_entity_a, RDF.type, OWL.Class) in ontologies[ont1]:
			# is_a_class = True
			alignments[prefix_pair].add((aligned_entity_a, OWL.equivalentClass, aligned_entity_b))
			alignments[prefix_pair].add((aligned_entity_a, RDF.type, entity_type))
			alignments[prefix_pair].add((aligned_entity_b, RDF.type, entity_type))

		# in case of property alignment
		else:
			# is_a_class = False
			alignments[prefix_pair].add((aligned_entity_a, OWL.equivalentProperty, aligned_entity_b))
			alignments[prefix_pair].add((aligned_entity_a, RDF.type, entity_type))
			alignments[prefix_pair].add((aligned_entity_b, RDF.type, entity_type))

	alignments[prefix_pair].serialize(destination=owl_alignments_dir + "/" + prefix_pair + ".ttl", format='turtle')



