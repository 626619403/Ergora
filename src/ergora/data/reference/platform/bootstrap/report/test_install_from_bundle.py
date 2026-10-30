"""CPU-only export-install integrity checks; no accounts or network required."""
import hashlib
import io
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from install_from_bundle import acquire, source_plan, temporal_binary, verify_bundle


class ExportInstallation(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def bundle(self):
        root = self.root / 'bundle'
        source = root / 'platform/example.py'
        source.parent.mkdir(parents=True)
        source.write_bytes(b'reviewed source\n')
        checksum = hashlib.sha256(source.read_bytes()).hexdigest()
        (root / 'BUNDLE-SHA256SUMS').write_text(checksum + '  platform/example.py\n')
        return root, source

    def test_tampered_file_is_rejected(self):
        root, source = self.bundle()
        source.write_text('changed')
        with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
            verify_bundle(root)

    def test_unlisted_file_is_rejected(self):
        root, source = self.bundle()
        (source.parent / 'unexpected.sh').write_text('exit 0')
        with self.assertRaisesRegex(ValueError, 'unlisted'):
            verify_bundle(root)

    def test_differing_existing_source_is_preserved(self):
        root, _ = self.bundle()
        target = self.root / 'installed/example.py'
        target.parent.mkdir()
        target.write_text('my local edits')
        with self.assertRaisesRegex(ValueError, 'Existing source differs'):
            source_plan(root, target.parent, verify_bundle(root))
        self.assertEqual(target.read_text(), 'my local edits')

    def test_destination_symlink_escape_is_rejected(self):
        root, _ = self.bundle()
        destination = self.root / 'installed'
        destination.mkdir()
        (destination / 'example.py').symlink_to(self.root / 'outside')
        with self.assertRaisesRegex(ValueError, 'escapes'):
            source_plan(root, destination, verify_bundle(root))

    def test_offline_cache_is_verified_then_copied(self):
        cache = self.root / 'cache'
        cache.write_bytes(b'pinned runtime')
        target = self.root / 'installed/runtime'
        checksum = hashlib.sha256(cache.read_bytes()).hexdigest()
        with patch('install_from_bundle.urlopen', side_effect=AssertionError('No network')):
            self.assertEqual(acquire(target, checksum, 'https://unused', cache, check=False), 'verified-cache')
        self.assertEqual(target.read_bytes(), cache.read_bytes())

    def test_bad_cache_is_rejected_without_copy(self):
        cache = self.root / 'cache'
        cache.write_text('wrong')
        target = self.root / 'runtime'
        with self.assertRaisesRegex(ValueError, 'cache checksum mismatch'):
            acquire(target, '0' * 64, 'https://unused', cache, check=False)
        self.assertFalse(target.exists())

    def test_check_never_downloads_or_creates_runtime(self):
        target = self.root / 'installed/runtime'
        with patch('install_from_bundle.urlopen', side_effect=AssertionError('No network')):
            self.assertEqual(acquire(target, '0' * 64, 'https://unused', None, check=True), 'needs-network-download')
        self.assertFalse(target.parent.exists())

    def test_temporal_extracts_only_binary_and_preserves_bad_existing_file(self):
        archive = self.root / 'temporal.tar.gz'
        with tarfile.open(archive, 'w:gz') as bundle:
            member = tarfile.TarInfo('temporal')
            member.size = 7
            bundle.addfile(member, io.BytesIO(b'runtime'))
        target = self.root / 'bin/temporal'
        temporal_binary(archive, target, check=True)
        self.assertFalse(target.exists())
        temporal_binary(archive, target)
        self.assertEqual(target.read_bytes(), b'runtime')
        target.write_bytes(b'user file')
        with self.assertRaisesRegex(ValueError, 'Existing Temporal binary'):
            temporal_binary(archive, target)
        self.assertEqual(target.read_bytes(), b'user file')


if __name__ == '__main__':
    unittest.main(verbosity=2)
