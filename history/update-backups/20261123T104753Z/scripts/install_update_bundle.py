"""Apply a flat-root SPOSE update bundle to an existing standalone library.

No 'remote/' wrapper is assumed. Only explicitly manifested scripts/docs are
replaced; pose ZIPs are copied into incoming/, never auto-imported. All previous
revision folders, source assets, and tracking databases are untouched.
"""
from __future__ import annotations
import argparse,datetime,hashlib,json,os,shutil,sys,tempfile
from pathlib import Path


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def checked_path(root,rel):
    if '\\' in rel or not rel or rel.startswith('/') or ':' in rel or any(p in ('..','.') for p in Path(rel).parts):
        raise ValueError('Unsafe relative path: '+rel)
    p=(Path(root)/rel).resolve()
    if not p.is_relative_to(Path(root).resolve()):raise ValueError('Path escapes target')
    return p


def verify_bundle(bundle):
    bundle=Path(bundle).resolve()
    meta=json.loads((bundle/'UPDATE-MANIFEST.json').read_text(encoding='utf-8'))
    if meta.get('kind')!='spose_rebuild_batch_update' or meta.get('schema_version')!=1 or meta.get('archive_root')!='flat':
        raise ValueError('Unsupported update manifest')
    for rel,expected in meta.get('bundle_files_sha256',{}).items():
        p=checked_path(bundle,rel)
        if not p.is_file() or p.is_symlink() or digest(p)!=expected:
            raise ValueError('Bundle inventory mismatch: '+rel)
    for group in ('replacements','pose_packages'):
        for rel,expected in meta[group].items():
            p=checked_path(bundle,rel)
            if not p.is_file() or p.is_symlink() or digest(p)!=expected:
                raise ValueError('Bundle member missing/corrupt: '+rel)
    return meta


def apply(bundle,library,dry_run=True):
    bundle=Path(bundle).resolve();library=Path(library).resolve()
    manifest=verify_bundle(bundle)
    project_path=library/'project.json'
    if not project_path.is_file():raise FileNotFoundError('Target is not SPOSE library root: missing project.json')
    project=json.loads(project_path.read_text(encoding='utf-8'))
    if project.get('project_id')!='SPOSE-REMOTE-LIBRARY':raise ValueError('Wrong project_id')
    source=library/'source/dataset.json'
    src=json.loads(source.read_text(encoding='utf-8'))
    if src.get('catalog_sha256')!=manifest['required_catalog_sha256']:
        raise ValueError('Catalog version mismatch; do not install over a different source')
    for required in manifest['required_assets']:
        if not checked_path(library,required).is_file():raise FileNotFoundError('Missing library dependency: '+required)
    template=checked_path(library,'pairs/CPL01/v001/template.blend')
    if digest(template)!=manifest['required_template_sha256']:
        raise ValueError('Shared pair template SHA-256 mismatch')
    if bundle==library or bundle.is_relative_to(library):
        raise ValueError('Extract updater separately, not into the live library')
    intended={}
    for rel in manifest['replacements']:
        intended[rel]=(checked_path(bundle,rel),checked_path(library,rel))
    for rel in manifest['pose_packages']:
        intended[rel]=(checked_path(bundle,rel),checked_path(library,'incoming/'+Path(rel).name))
    # Surgical project setting migration: never replace other user project settings.
    desired_project=json.loads(json.dumps(project))
    desired_project.setdefault('portable_handoff',{})['archive_root']='flat'
    project_needs_update=desired_project != project
    conflicts=[];already=[];changes=[]
    for rel,(srcfile,dst) in intended.items():
        if dst.exists():
            if dst.is_symlink() or not dst.is_file():conflicts.append(str(dst))
            elif digest(srcfile)==digest(dst):already.append(str(dst))
            elif rel in manifest['pose_packages']:conflicts.append(str(dst))
            else:changes.append(str(dst))
        else:changes.append(str(dst))
    if conflicts:raise ValueError('Refusing overwrite of existing different package/nonfile: '+str(conflicts))
    report={'ok':True,'mode':'dry_run' if dry_run else 'applied',
            'library':str(library),'replacement_count':len(manifest['replacements']),
            'pose_package_count':len(manifest['pose_packages']),
            'would_write':changes,'identical_skipped':already,
            'project_portable_handoff_archive_root':{'before':project.get('portable_handoff',{}).get('archive_root'),'after':'flat','will_update':project_needs_update},
            'tracker_untouched':True,
            'source_untouched':True,'historic_pose_revisions_untouched':True}
    if dry_run:return report
    if not changes and not project_needs_update:
        report['mode']='already_installed'
        report['already_installed']=True
        return report
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup=library/'history'/'update-backups'/stamp
    if backup.exists():raise FileExistsError(backup)
    rollback=[]
    try:
        if project_needs_update:
            dst=project_path
            project_backup=checked_path(backup,'project.json')
            project_backup.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(dst,project_backup)
            rollback.append((dst,project_backup))
            fd,tmp=tempfile.mkstemp(prefix='spose-stage-',dir=dst.parent)
            try:
                with os.fdopen(fd,'w',encoding='utf-8') as file:
                    json.dump(desired_project,file,indent=2,ensure_ascii=False)
                    file.write('\n')
                os.replace(tmp,dst)
            finally:
                if os.path.exists(tmp):os.unlink(tmp)

        # All checks and incoming collision detection are complete before mutation.
        for rel,(srcfile,dst) in intended.items():
            if dst.is_file() and digest(dst)==digest(srcfile):continue
            if dst.exists():
                backup_file=checked_path(backup,rel)
                backup_file.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(dst,backup_file)
                rollback.append((dst,backup_file))
            else:rollback.append((dst,None))
            dst.parent.mkdir(parents=True,exist_ok=True)
            fd,tmp=tempfile.mkstemp(prefix='spose-stage-',dir=dst.parent)
            try:
                with os.fdopen(fd,'wb') as f:f.write(srcfile.read_bytes())
                os.replace(tmp,dst)
            finally:
                if os.path.exists(tmp):os.unlink(tmp)
        receipt_record={'schema_version':1,'installed_at_utc':stamp,'bundle_id':manifest['bundle_id'],
             'bundle_manifest_sha256':digest(bundle/'UPDATE-MANIFEST.json'),
             'replacements':list(manifest['replacements']),
             'pose_packages':list(manifest['pose_packages']),
             'project_archive_root_migrated':project_needs_update,
             'blender_tested_during_install':False,
             'note':'Release manifest is a historical full-archive snapshot; use this receipt for incremental installs.'}
        receipt=backup/'INSTALL-RECEIPT.json';receipt.parent.mkdir(parents=True,exist_ok=True)
        receipt.write_text(json.dumps(receipt_record,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        current=library/'CURRENT-INSTALL.json'
        old_current=None
        if current.exists():
            if not current.is_file() or current.is_symlink():raise ValueError('CURRENT-INSTALL.json is not a regular file')
            old_current=checked_path(backup,'CURRENT-INSTALL.json')
            old_current.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(current,old_current)
        rollback.append((current,old_current))
        fd,tmp=tempfile.mkstemp(prefix='spose-stage-',dir=current.parent)
        try:
            with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(receipt_record,f,indent=2,ensure_ascii=False);f.write('\n')
            os.replace(tmp,current)
        finally:
            if os.path.exists(tmp):os.unlink(tmp)
        report['backup_dir']=str(backup)
        report['current_install_manifest']=str(current)
        return report
    except Exception:
        for dest,old in reversed(rollback):
            try:
                if old and old.is_file():shutil.copy2(old,dest)
                elif dest.is_file():dest.unlink()
            except Exception:pass
        raise


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle',type=Path,default=Path(__file__).resolve().parents[1],help='Extracted batch folder')
    p.add_argument('--library',type=Path,required=True,help='Folder containing project.json (name arbitrary)')
    p.add_argument('--apply',action='store_true',help='Perform changes; default only checks and previews changes')
    a=p.parse_args()
    print(json.dumps(apply(a.bundle,a.library,not a.apply),indent=2))
if __name__=='__main__':main()
