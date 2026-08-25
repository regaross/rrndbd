import uproot
from uproot import open
import numpy as np
import awkward as ak
import pandas as pd



class Simulation:

    def __init__(self, filename) -> None:
        self.file = open(filename)
        self.filename = filename
        self.trees = []

        ### This sets the TTrees as class objects... a bit easier to navigate.
        for name, obj in self.file.items():
            if isinstance(obj, uproot.behaviors.TTree.TTree):
                setattr(self, obj.name, obj)
                self.trees.append(obj.name)


        if hasattr(self, 'eventBiasing'):      # Ensure that it has the adjacencyList attribute
            if ak.sum(self.eventBiasing['nodes'].array()) > 0: # Ensure that the sum of the histories > 0 (otherwise no importance boundaries were crossed)
                self.boosted = True 
        else:
             self.boosted = False

    def _boost_error(self, message_add_on = ''):
        '''A simple function that should be run at the beginning of every functtion '''
        if not self.boosted:
                    raise RuntimeError("Simulation is not boosted.", '\n', message_add_on)



    def seetrees(self) -> None:
        '''Displays the structure of the Ttree'''

        for branch in self.file.keys():
            print(f"{branch:<20}{'#'*40}")

            for leaf in self.file[branch].keys():
                obj = self.file[branch][leaf]
                print(f"{'\t'}{leaf:<35}{obj.typename:<30}{obj.num_entries}")


    def keys(self):
        return self.trees

    def __getitem__(self, key):
        return self.file[key]
    

    def deposits_by_lineage(self):
        '''Attach each history's deposit hits onto eventBiasing (one row per lineage).'''

        self._boost_error()

        print('Expect this to take 5+ minutes.')

        # Instantiate the tree branches as arrays
        boost = self.eventBiasing.arrays()
        deps = self.deposits.arrays()

        # Join on (RunID, EventID): eventBiasing is 1-to-many with deposits
        dep_index = pd.MultiIndex.from_arrays(
            [ak.to_numpy(deps["RunID"]), ak.to_numpy(deps["EventID"])],
            names=["RunID", "EventID"],
        )
        boost_index = pd.MultiIndex.from_arrays(
            [ak.to_numpy(boost["RunID"]), ak.to_numpy(boost["EventID"])],
            names=["RunID", "EventID"],
        )
        idx = dep_index.get_indexer(boost_index)

        # Use node only to build the mask — do not expand the other branches
        node_counts = ak.to_numpy(ak.num(deps["node"], axis=1))
        offsets = np.empty(len(node_counts) + 1, dtype=np.int64)
        offsets[0] = 0
        offsets[1:] = np.cumsum(node_counts)

        node = deps["node"][idx]

        # Allowed nodes for this history: the boosted path plus folded-in brem nodes
        allowed = ak.concatenate([boost["nodes"], boost["bremNodes"]], axis=1)

        # Make a mask that looks at the indices where deps['node'] is in the history nodes
        mask = ak.any(
            node[:, :, None] == allowed[:, None, :],
            axis=-1,
        )

        # Pointers into the original (un-replicated) deposit hits
        steps = ak.local_index(node, axis=1)[mask]
        flat_i = ak.flatten(steps + offsets[idx])
        kept = ak.num(steps, axis=1)

        # Start from eventBiasing; attach masked deposit hits (skip keys already on boost)
        skip = {"RunID", "EventID", "trackWeight"}
        out = {field: boost[field] for field in boost.fields}
        for field in deps.fields:
            if field in skip:
                continue
            out[field] = ak.unflatten(ak.flatten(deps[field], axis=1)[flat_i], kept)

        # Important: avoid deep nested broadcasting between scalar and jagged fields
        return ak.zip(out, depth_limit=1)














########                                                               ########
###########         Much of what's below here is deprecated         ########### 
#######                                                                ########

#     def lineage_nodes(self, primary_index) -> list[np.ndarray]:
#         '''Given the primary particle index, this returns the nodes that belong to the particle. These nodes are assembled to reproduce deposits, etc'''

#         file = self.file

#         # These are the sequences of nodes that particles follow
#         node_paths = file['adjacencyList']['history'].array()[primary_index]

#         # Each sequence of nodes in a lineage starts with 0
#         split_indices = np.where(node_paths == 0)[0]
        
#         return np.split(node_paths, split_indices[1:])


#     def boosted_indices(self) -> np.ndarray:
#         '''For the purpose of bug-testing we may want only the particles that underwent boosting (crossed an importance boundary and were cloned)
#         This function finds all of those particles that were cloned and returns their primary indices or "EventID"s '''

#         return np.where(np.sum(self.file['adjacencyList']['history'].array(), axis = 1) > 0)[0]


# def split_histories(flat_history):
#     """
#     Split adjacencyList.history on leading 0 markers into independent paths.

#     Example: [0, 1, 0, 2, 3, 0, 2, 5] -> [[0, 1], [0, 2, 3], [0, 2, 5]]
#     """
#     flat = list(flat_history) if flat_history is not None else []
#     if len(flat) == 0:
#         return [[0]]

#     paths = []
#     current = None
#     for n in flat:
#         n = int(n)
#         if n == 0:
#             if current is not None:
#                 paths.append(current)
#             current = [0]
#         else:
#             if current is None:
#                 current = [0, n]
#             else:
#                 current.append(n)

#     if current is not None:
#         paths.append(current)

#     return paths if paths else [[0]]


# def file_looks_biased(file, deposits):
#     has_adj = "adjacencyList" in file
#     has_node = "node" in deposits.keys()
#     has_eb = "eventBiasing" in file
#     return has_adj and has_node and has_eb


# def validate_biased_mode(root_file, file, deposits, biased):
#     looks_biased = file_looks_biased(file, deposits)
#     has_adj = "adjacencyList" in file
#     has_node = "node" in deposits.keys()
#     has_eb = "eventBiasing" in file

#     if biased:
#         if not has_adj and not has_node and not has_eb:
#             raise RuntimeError(
#                 f"{root_file}: file looks unbiased "
#                 "(no adjacencyList/node/eventBiasing); refuse --biased. "
#                 "Pass --unbiased for this file."
#             )
#         if has_adj and not has_node:
#             raise RuntimeError(
#                 f"{root_file}: adjacencyList is present but deposits has no "
#                 "'node' branch; cannot build full-path history masks under "
#                 "--biased."
#             )
#         if not has_adj and has_node:
#             raise RuntimeError(
#                 f"{root_file}: deposits has 'node' but adjacencyList is "
#                 "missing; refuse --biased."
#             )
#         if has_adj and has_node and not has_eb:
#             raise RuntimeError(
#                 f"{root_file}: adjacencyList/node present but eventBiasing "
#                 "is missing; cannot assign lineage trackWeights under "
#                 "--biased."
#             )
#         if not looks_biased:
#             raise RuntimeError(
#                 f"{root_file}: file does not look biased "
#                 "(need adjacencyList, deposits.node, and eventBiasing); "
#                 "refuse --biased."
#             )
#     else:
#         if looks_biased or (has_adj and has_node):
#             raise RuntimeError(
#                 f"{root_file}: file has biasing trees (adjacencyList/node); "
#                 "pass --biased to expand lineages. Refuse --unbiased."
#             )


# def load_histories_by_event_id(file):
#     """
#     Preload adjacencyList keyed by EventID -> list of node paths.

#     adjacencyList only stores `history` (one row per primary, same order as
#     the event tree). Join EventID from the event tree by entry index.
#     """
#     adj = file["adjacencyList"]
#     event = file["event"]
#     histories = adj["history"].array(library="np")

#     if "EventID" in event.keys():
#         eids = event["EventID"].array(library="np")
#     else:
#         eids = np.arange(len(histories))

#     if len(eids) != len(histories):
#         raise RuntimeError(
#             "adjacencyList and event trees have different entry counts "
#             f"({len(histories)} vs {len(eids)}); cannot join histories."
#         )

#     histories_by_eid = {}
#     for eid, hist in zip(eids, histories):
#         histories_by_eid[int(eid)] = split_histories(hist)
#     return histories_by_eid


# def load_history_weights_by_event_id(file):
#     """
#     Preload eventBiasing.trackWeight keyed by EventID -> list of weights.

#     One weight per history, in the same order as adjacencyList paths for that
#     primary. Matches Geant4's min trackWeight along each path (leaf / highest
#     node after importance crossings).
#     """
#     eb = file["eventBiasing"]
#     arrays = eb.arrays(["EventID", "trackWeight"], library="np")
#     weights_by_eid = {}
#     for eid, w in zip(arrays["EventID"], arrays["trackWeight"]):
#         weights_by_eid.setdefault(int(eid), []).append(float(w))
#     return weights_by_eid