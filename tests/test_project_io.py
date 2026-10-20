import importlib.util,json,os,tempfile,unittest,zipfile
from pathlib import Path
path=Path(__file__).resolve().parents[1]/'cura_plugin/CuraMcpBridge/project_io.py'
spec=importlib.util.spec_from_file_location('project_io',path)
io=importlib.util.module_from_spec(spec);spec.loader.exec_module(io)

def writer(stream):
    with zipfile.ZipFile(stream,'w') as archive:
        archive.writestr('3D/3dmodel.model','<model/>')
        archive.writestr('Cura/test_user.inst.cfg','[values]\nmaterial_flow = 115\n')
    return True

class ProjectIOTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
    def create(self,name='original.3mf'):
        target=self.root/name
        plan=io.plan_save({'mode':'save_as','file_name':name},None,str(self.root))
        io.atomic_project_write(plan,writer)
        return str(target)
    def test_save_same_name_and_folder(self):
        target=self.create();plan=io.plan_save({'mode':'save'},target,str(self.root))
        self.assertIsNotNone(plan['expected_sha256'])
        self.assertGreater(io.atomic_project_write(plan,writer)['bytes'],0)
    def test_save_as_same_folder_and_new_folder(self):
        current=self.create()
        renamed=io.plan_save({'mode':'save_as','file_name':'renamed'},current,str(self.root))
        self.assertEqual(renamed['file_path'],os.path.join(os.path.realpath(self.root),'renamed.3mf'))
        io.atomic_project_write(renamed,writer)
        nested=self.root/'new'/'nested'
        with self.assertRaisesRegex(ValueError,'folder does not exist'):
            io.plan_save({'mode':'save_as','folder':str(nested)},current,str(self.root))
        plan=io.plan_save({'mode':'save_as','folder':str(nested),'create_folder':True},current,str(self.root))
        self.assertFalse(nested.exists(),'planning must not create folders')
        io.atomic_project_write(plan,writer)
        self.assertTrue((nested/'original.3mf').is_file())
    def test_save_as_never_overwrites_and_save_rejects_changed_disk(self):
        current=self.create()
        with self.assertRaisesRegex(ValueError,'already exists'):
            io.plan_save({'mode':'save_as','file_name':'original.3mf'},current,str(self.root))
        plan=io.plan_save({'mode':'save'},current,str(self.root))
        Path(current).write_bytes(b'changed by another program')
        with self.assertRaisesRegex(ValueError,'changed on disk'):
            io.atomic_project_write(plan,writer)
        self.assertEqual(Path(current).read_bytes(),b'changed by another program')
    def test_failure_does_not_damage_original_or_leave_partial(self):
        current=self.create();before=Path(current).read_bytes()
        plan=io.plan_save({'mode':'save'},current,str(self.root))
        def failed(stream):stream.write(b'partial');return False
        with self.assertRaisesRegex(RuntimeError,'writer reported failure'):io.atomic_project_write(plan,failed)
        self.assertEqual(Path(current).read_bytes(),before)
        self.assertEqual(list(self.root.glob('.cura-mcp-save-*')),[])
        def invalid(stream):stream.write(b'not a zip');return True
        with self.assertRaises(zipfile.BadZipFile):io.atomic_project_write(plan,invalid)
        self.assertEqual(Path(current).read_bytes(),before)
    def test_paths_unknown_current_and_concurrent_creation(self):
        with self.assertRaisesRegex(ValueError,'No known current project'):
            io.plan_save({'mode':'save'},None,str(self.root))
        for name in ('../escape','a/b','a\\b'):
            with self.assertRaises(ValueError):io.plan_save({'mode':'save_as','file_name':name},None,str(self.root))
        plan=io.plan_save({'mode':'save_as','file_name':'appeared'},None,str(self.root))
        Path(plan['file_path']).write_bytes(b'external')
        with self.assertRaisesRegex(ValueError,'appeared after confirmation'):io.atomic_project_write(plan,writer)
        self.assertEqual(Path(plan['file_path']).read_bytes(),b'external')
        info=io.path_info(plan['file_path']);self.assertTrue(info['readable'])
        self.assertEqual(io.path_info(str(self.root/'missing'))['error_type'],'FileNotFoundError')

if __name__=='__main__':unittest.main()
