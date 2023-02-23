# This script identifies more instance alignments across pairs of ontologies, that allow us to
from data_utils import *

from rdflib import URIRef, Graph
from collections import defaultdict


def clean_instance_alignments(updated_alignments_dict_format, new_alignments, alignment_conflicts):
    clean_new_alignments = set()
    # checking for alignment conflicts: if we suggest a new alignment for a URI that is already aligned
    for ontology_1_entity_URI, ontology_2_entity_URI in new_alignments:
        # in case of conflict:
        if ontology_1_entity_URI in updated_alignments_dict_format:
            old_alignment = updated_alignments_dict_format[ontology_1_entity_URI]
            # update conflict alignment dictionary
            alignment_conflicts[ontology_1_entity_URI] = alignment_conflicts[ontology_1_entity_URI].union(
                {old_alignment, ontology_2_entity_URI})
        elif ontology_2_entity_URI in updated_alignments_dict_format:
            old_alignment = updated_alignments_dict_format[ontology_2_entity_URI]
            # update conflict alignment dictionary
            alignment_conflicts[ontology_2_entity_URI] = alignment_conflicts[ontology_2_entity_URI].union(
                {old_alignment, ontology_1_entity_URI})
        else:
            # if there are no conflicts regarding this alignment, we can just add it and move one.
            clean_new_alignments.add((ontology_1_entity_URI, ontology_2_entity_URI))
            updated_alignments_dict_format[ontology_1_entity_URI] = ontology_2_entity_URI
            updated_alignments_dict_format[ontology_2_entity_URI] = ontology_1_entity_URI

    return clean_new_alignments, alignment_conflicts, updated_alignments_dict_format


def get_common_instances_across_ontologies(ontology_1, ontology_2, method_keyword_set,
                                           provided_aligned_individuals=None, provided_aligned_properties=None,
                                           provided_handcrafted_aligned_properties=None, prefix_pair=None):
    '''
    applies some vanilla instance matching methods on two ontologies and returns a set of aligned URIs.
    An instance is defined as an URI that is rdf:type owl:NamedIndividual
    method keyword options and their meaning:
    - same_URI : identical URIs (o:x, o:x)
    - same_name : same name, after striping the URI from its namespace (o1:x, o2:x)
    - same_relation : o1:x == o2:y if (common_entity, common_relation, o1:x) , (common_entity, common_relation, o2:y)
    - same_relation_handcrafted : o1:x == o2:y if (common_entity, common_relation, o1:x) , (common_entity, common_relation, o2:y)
    - handcrafted_queries : handcrafted complex SPARQL queries to propose instance alignments
    :param ontology_1: a rdflib.Graph instance
    :param ontology_2:  a rdflib.Graph instance
    :param method_keyword_set: "same_URI", "same_name", "same_relation", "same_relation_handcrafted", "handcrafted_queries" ,
    :return: aligned_individuals = set((URI1, URI2), (URI3, URI4), ...)
    '''

    rdf_type = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
    owl_named_individual = URIRef("http://www.w3.org/2002/07/owl#NamedIndividual")

    # retrieve all named individuals
    ontology_1_individuals = set()
    ontology_2_individuals = set()
    matching_form_to_original_URI_dict_ontology_1 = {}
    matching_form_to_original_URI_dict_ontology_2 = {}

    for named_individual_instance in ontology_1.subjects(rdf_type, owl_named_individual):
        ontology_1_individuals.add(named_individual_instance)
    for named_individual_instance in ontology_2.subjects(rdf_type, owl_named_individual):
        ontology_2_individuals.add(named_individual_instance)

    if "same_URI" in method_keyword_set:
        for named_individual_instance in ontology_1_individuals:
            matching_form_to_original_URI_dict_ontology_1[named_individual_instance] = named_individual_instance
        for named_individual_instance in ontology_2_individuals:
            matching_form_to_original_URI_dict_ontology_2[named_individual_instance] = named_individual_instance

    if "same_name" in method_keyword_set:
        for named_individual_instance in ontology_1_individuals:
            instance_name_striped_from_namespace = str(named_individual_instance).split("#")[-1]
            # if another entity has already been registered with the same matching form in this ontology, (same name, different namespaces), then we report an error!
            if instance_name_striped_from_namespace in matching_form_to_original_URI_dict_ontology_1:
                error_message = "Different entities were attempted to be registered under the same name! Matching method: stripping namespace.\n"
                other_URI = matching_form_to_original_URI_dict_ontology_1[instance_name_striped_from_namespace]
                error_message += f"{other_URI}  --  {named_individual_instance}"
                raise ValueError(error_message)
            matching_form_to_original_URI_dict_ontology_1[
                instance_name_striped_from_namespace] = named_individual_instance
        for named_individual_instance in ontology_2_individuals:
            instance_name_striped_from_namespace = str(named_individual_instance).split("#")[-1]
            # if another entity has already been registered with the same matching form in this ontology, (same name, different namespaces), then we report an error!
            if instance_name_striped_from_namespace in matching_form_to_original_URI_dict_ontology_2:
                error_message = "Different entities were attempted to be registered under the same name! Matching method: stripping namespace.\n"
                other_URI = matching_form_to_original_URI_dict_ontology_2[instance_name_striped_from_namespace]
                error_message += f"{other_URI}  --  {named_individual_instance}"
                raise ValueError(error_message)
            matching_form_to_original_URI_dict_ontology_2[
                instance_name_striped_from_namespace] = named_individual_instance

    form_based_alignments = set()

    if provided_aligned_individuals is not None:
        form_based_alignments += provided_aligned_individuals

    for ontology_1_entity_form in matching_form_to_original_URI_dict_ontology_1:
        if ontology_1_entity_form in matching_form_to_original_URI_dict_ontology_2:
            ontology_1_entity_URI = matching_form_to_original_URI_dict_ontology_1[ontology_1_entity_form]
            # since the forms are matching, then we can use ontology_1_entity_form to retrieve the corresponding URI in ontology 2
            ontology_2_entity_URI = matching_form_to_original_URI_dict_ontology_2[ontology_1_entity_form]
            alignment = (ontology_1_entity_URI, ontology_2_entity_URI)
            form_based_alignments.add(alignment)

    formed_based_matchings_dict_format = dict()
    URIs_of_certain_alignments = set()
    for ontology_1_entity_URI, ontology_2_entity_URI in form_based_alignments:
        # identity mappings can be found here from the "same_URI" option, so no need to check for errors.
        formed_based_matchings_dict_format[ontology_1_entity_URI] = ontology_2_entity_URI
        formed_based_matchings_dict_format[ontology_2_entity_URI] = ontology_1_entity_URI
        URIs_of_certain_alignments.add(ontology_1_entity_URI)
        URIs_of_certain_alignments.add(ontology_2_entity_URI)

    all_alignments = form_based_alignments.copy()

    searched_alignments_and_relations = set()

    if "same_relation" in method_keyword_set or "same_relation_handcrafted" in method_keyword_set:
        relation_alignments_to_use = set()
        if "same_relation" in method_keyword_set:
            if provided_aligned_properties is None:
                raise ValueError(
                    "On aligning instances, 'same_relation' was selected but no property alignments were provided!")
            else:
                relation_alignments_to_use = provided_aligned_properties
        if "same_relation_handcrafted" in method_keyword_set:
            if provided_handcrafted_aligned_properties is None:
                raise ValueError(
                    "On aligning instances, 'same_relation_handcrafted' was selected but no handcrafted property alignments were provided!")
            else:
                relation_alignments_to_use += provided_handcrafted_aligned_properties

        alignment_conflicts = defaultdict(set)
        more_cases_found = True
        all_alignments_dict_format = formed_based_matchings_dict_format.copy()
        clean_new_relationship_alignments = set()
        clean_relationship_alignments = set()
        # Maybe let's not get into the loop version yet, cause a proper implementation would require recursion.
        while more_cases_found:
            new_alignments = set()
            # for every so-far known entity alignment
            for ontology_1_entity_URI, ontology_2_entity_URI in all_alignments:
                # for every known property alignment
                for relation_1_URI, relation_2_URI in relation_alignments_to_use:
                    relation_1_URI, relation_2_URI = URIRef(relation_1_URI), URIRef(relation_2_URI)

                    # we don't want to keep on counting the same candidate match over all iterations
                    search_combination = (ontology_1_entity_URI, ontology_2_entity_URI, relation_1_URI, relation_2_URI)
                    if search_combination in searched_alignments_and_relations:
                        continue

                    searched_alignments_and_relations.add(search_combination)
                    # searching for matching objects
                    ontology_1_objects = set(ontology_1.objects(ontology_1_entity_URI, relation_1_URI))
                    ontology_2_objects = set(ontology_2.objects(ontology_2_entity_URI, relation_2_URI))

                    for object_1 in ontology_1_objects:
                        for object_2 in ontology_2_objects:
                            if object_1 not in URIs_of_certain_alignments and object_2 not in URIs_of_certain_alignments:
                                candidate_alignment = (object_1, object_2)
                                if candidate_alignment not in all_alignments:
                                    new_alignments.add(candidate_alignment)

                    # searching for matching subjects
                    ontology_1_subjects = set(ontology_1.subjects(relation_1_URI, ontology_1_entity_URI))
                    ontology_2_subjects = set(ontology_2.subjects(relation_2_URI, ontology_2_entity_URI))
                    for subject_1 in ontology_1_subjects:
                        for subject_2 in ontology_2_subjects:
                            if subject_1 not in URIs_of_certain_alignments and subject_2 not in URIs_of_certain_alignments:
                                candidate_alignment = (subject_1, subject_2)
                                if candidate_alignment not in all_alignments:
                                    new_alignments.add(candidate_alignment)

            more_cases_found = True if len(new_alignments) > 0 else False

            clean_new_relationship_alignments, alignment_conflicts, all_alignments_dict_format = clean_instance_alignments(
                all_alignments_dict_format, new_alignments, alignment_conflicts)
            all_alignments = all_alignments.union(clean_new_relationship_alignments)

            clean_relationship_alignments = clean_relationship_alignments.union(clean_new_relationship_alignments)
            alignment_conflicts_pair_set = set()
            for URI_1 in alignment_conflicts:
                for URI_2 in alignment_conflicts[URI_1]:
                    alignment_conflicts_pair_set.add((URI_1, URI_2))
            clean_relationship_alignments = clean_relationship_alignments - alignment_conflicts_pair_set

    else:
        all_alignments_dict_format = dict()
        alignment_conflicts = set()

    if "handcrafted_queries" in method_keyword_set:
        alignments_from_handcrafted_queries = run_sparql_queries_for_instance_matching_on_ontology_pair(ontology_1,
                                                                                                        ontology_2,
                                                                                                        prefix_pair)

        clean_alignments_from_handcrafted_queries, alignment_conflicts, all_alignments_dict_format = clean_instance_alignments(
            all_alignments_dict_format, alignments_from_handcrafted_queries, alignment_conflicts)

        all_alignments = all_alignments.union(clean_alignments_from_handcrafted_queries)

    return all_alignments


def run_sparql_queries_for_instance_matching_on_ontology_pair(ontology_1, ontology_2, prefix_pair):
    '''
    # In this function, we define the sparql queries that help us identify more instance alignments for the extended dataset construction
    # These are mentioned as "complex queries" on the paper. In the code they are referred to as "handcrafted queries"
    '''
    ontology_pair_instance_matching_queries_dict = {
        "cmt-iasted":
            [
                '''
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        PREFIX cmt: <http://cmt#>
        PREFIX confOf: <http://confOf#>
        PREFIX edas: <http://edas#>
        PREFIX ekaw: <http://ekaw#>
        PREFIX iasted: <http://iasted#>
        PREFIX sigkdd: <http://sigkdd#>
        PREFIX conference: <http://conference#>

        SELECT DISTINCT ?cmt_review ?iasted_review WHERE {
          ?iasted_review rdf:type iasted:Review .
          ?iasted_review iasted:is_writen_by ?common_reviewer .
          ?cmt_review cmt:writtenBy ?common_reviewer .
          ?cmt_review rdf:type cmt:Review .
        }    '''
            ],

        "confof-ekaw":
            [

                '''
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        PREFIX cmt: <http://cmt#>
        PREFIX confOf: <http://confOf#>
        PREFIX edas: <http://edas#>
        PREFIX ekaw: <http://ekaw#>
        PREFIX iasted: <http://iasted#>
        PREFIX sigkdd: <http://sigkdd#>
        PREFIX conference: <http://conference#>

        SELECT DISTINCT ?confof_paper ?ekaw_paper WHERE {
            ?confof_paper rdf:type confOf:Contribution .
            ?confof_paper confOf:writtenBy ?author .

            ?ekaw_paper ekaw:writtenBy ?author.
            ?ekaw_paper rdf:type ekaw:Paper .
        }      '''
            ],

        "edas-iasted":
            [
                '''
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        PREFIX cmt: <http://cmt#>
        PREFIX confOf: <http://confOf#>
        PREFIX edas: <http://edas#>
        PREFIX ekaw: <http://ekaw#>
        PREFIX iasted: <http://iasted#>
        PREFIX sigkdd: <http://sigkdd#>
        PREFIX conference: <http://conference#>

        SELECT DISTINCT ?edas_paper ?iasted_paper WHERE {
          ?edas_paper rdf:type edas:Paper.
          ?edas_paper edas:isWrittenBy ?author.

          ?iasted_paper rdf:type iasted:Submission .
          ?iasted_paper iasted:is_writen_by ?author .
        }   '''
            ],

        "ekaw-iasted":

            [
                """
                PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        PREFIX cmt: <http://cmt#>
        PREFIX confOf: <http://confOf#>
        PREFIX edas: <http://edas#>
        PREFIX ekaw: <http://ekaw#>
        PREFIX iasted: <http://iasted#>
        PREFIX sigkdd: <http://sigkdd#>
        PREFIX conference: <http://conference#>

        SELECT DISTINCT ?ekaw_review ?iasted_review WHERE {
          ?ekaw_review rdf:type ekaw:Review .
          ?ekaw_review ekaw:writtenBy ?common_reviewer .

          ?iasted_review rdf:type iasted:Review .
          ?iasted_review iasted:is_writen_by ?common_reviewer .

        }   """
            ]

    }

    merged_ontologies = ontology_1 + ontology_2

    alignments_set = set()
    if prefix_pair in ontology_pair_instance_matching_queries_dict:
        for query_text in ontology_pair_instance_matching_queries_dict[prefix_pair]:
            results = merged_ontologies.query(query_text)
            alignments_set = alignments_set.union(set(results))

    return alignments_set

def generate_instance_alignments(reasoned_ontologies_dir, reference_alignments_dir,
                                 handcrafted_reference_alignments_dir, out_alignments_dir):

    ontology_prefixes_list = get_all_ontology_prefixes()
    all_prefix_pairs = get_all_prefix_pairs()
    prefix_to_ontology_dict = {}

    # read all ontologies
    for ontology_prefix in ontology_prefixes_list:
        prefix_to_ontology_dict[ontology_prefix] = Graph()
        prefix_to_ontology_dict[ontology_prefix].parse(reasoned_ontologies_dir + "/" + ontology_prefix + ".owl")

    # make sure the directory exists
    if not os.path.isdir(out_alignments_dir):
        os.mkdir(out_alignments_dir)

    for prefix_pair in all_prefix_pairs:
        prefix_1, prefix_2 = prefix_pair.split("-")

        ontology_1 = prefix_to_ontology_dict[prefix_1]
        ontology_2 = prefix_to_ontology_dict[prefix_2]

        # see if we know equivalency pairs among these classes, including property equivalencies
        equivalent_classes, equivalent_properties = load_ontology_alignments(ont_1_prefix=prefix_1,
                                                                             ont_2_prefix=prefix_2,
                                                                             dir_path=reference_alignments_dir)
        # in case there is a file with handwritten Property equivalencies, then read them as well.
        try:
            _, handcrafted_equivalent_properties = load_ontology_alignments(ont_1_prefix=prefix_1,
                                                                            ont_2_prefix=prefix_2,
                                                                            dir_path=handcrafted_reference_alignments_dir)
        except ValueError:
            handcrafted_equivalent_properties = []

        produced_alignments = get_common_instances_across_ontologies(ontology_1, ontology_2,
                                                                     {"same_name", "same_relation",
                                                                      "same_relation_handcrafted",
                                                                      "handcrafted_queries"},
                                                                     provided_aligned_properties=equivalent_properties,
                                                                     provided_handcrafted_aligned_properties=handcrafted_equivalent_properties,
                                                                     prefix_pair=prefix_pair)

        with open(out_alignments_dir + "/" + prefix_pair + ".csv", "w") as produced_alignments_out_file:
            for URI_1, URI_2 in produced_alignments:
                produced_alignments_out_file.write(str(URI_1) + "," + str(URI_2) + "\n")

if __name__ == '__main__':
    generate_instance_alignments(
        reasoned_ontologies_dir="dataset/reasoned_ontologies",
        reference_alignments_dir="dataset/reference_alignments_owl",
        handcrafted_reference_alignments_dir="data_preparation/hand_picked_property_based_alignments",
        out_alignments_dir="dataset/produced_instance_alignments")
