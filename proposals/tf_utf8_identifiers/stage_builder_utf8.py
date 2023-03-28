# Copyright 2023 NVIDIA CORPORATION
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pxr import Usd, UsdGeom, Sdf
​
stage = Usd.Stage.CreateNew("./complicated.usd")
reference = Usd.Stage.CreateNew("./reference.usd")
reference_scope = UsdGeom.Scope.Define(reference, "/reference")
reference.SetDefaultPrim(reference_scope.GetPrim())
reference_scope.GetPrim().CreateAttribute("test", Sdf.ValueTypeNames.Float)
reference.GetRootLayer().Save()
​
for i in range(100):
    root_path = Sdf.Path(f"/root_{i}")
    root = UsdGeom.Scope.Define(stage, root_path)
    root.GetPrim().CreateAttribute("attr1", Sdf.ValueTypeNames.Int)
    root.GetPrim().CreateAttribute("attr2", Sdf.ValueTypeNames.Int)
    root.GetPrim().CreateAttribute("attr3", Sdf.ValueTypeNames.IntArray)
    root.GetPrim().CreateAttribute("attr4", Sdf.ValueTypeNames.IntArray)
    for j in range(100):
        child_path = root_path.AppendChild(f"child_{j}")
        child = UsdGeom.Scope.Define(stage, child_path)
        rel = child.GetPrim().CreateRelationship("rel1")
        rel.SetTargets([root_path])
        for k in range(10):
            grandchild_path = child_path.AppendChild(f"grandchild_{k}")
            grandchild = UsdGeom.Scope.Define(stage, grandchild_path)
            rel = grandchild.GetPrim().CreateRelationship("rel2")
            rel.SetTargets([child_path])
            for m in range(10):
                greatgrandchild_path = grandchild_path.AppendChild(f"greatgrandchild_{m}")
                greatgrandchild = UsdGeom.Scope.Define(stage, greatgrandchild_path)
                rel = greatgrandchild.GetPrim().CreateRelationship("rel3")
                rel.SetTargets([grandchild_path])
                for n in range(12):
                    greatgrandchild.GetPrim().CreateAttribute(f"primvars:primvar{n}", Sdf.ValueTypeNames.IntArray)
                references = greatgrandchild.GetPrim().GetReferences()
                references.AddReference("./reference.usd")
​
stage.GetRootLayer().Save()