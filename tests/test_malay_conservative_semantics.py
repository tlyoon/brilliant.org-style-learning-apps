"""Adversarial source-free tests for exact private Malay physics repair."""
from copy import deepcopy
from pathlib import Path
from hashlib import sha256
import json
import tempfile
import unittest
from unittest.mock import patch

from app_generator.validation.malay_conservative_semantics import (
    RULES,_malay_misconceptions,_node,patch_private_semantics,
    emit_versioned_private_candidate,
)


def synthetic_package():
    data={"prerequisites":[{} for _ in range(3)],
          "activities":[{"id":"synthetic-"+str(i)} for i in range(18)]}
    for pointer,old,_new in RULES:
        obj=data
        parts=pointer.strip("/").split("/")
        for key in parts[:-1]:
            if isinstance(obj,list):
                index=int(key)
                obj=obj[index]
            else:
                if key not in obj:obj[key]=[] if key in ("hints","items") else {}
                obj=obj[key]
            # Pre-size lists at the point they are traversed.
            if isinstance(obj,list):
                following=parts[parts.index(key)+1]
                if following.isdigit():
                    while len(obj)<=int(following):obj.append({})
        key=parts[-1]
        obj[key]=(obj.get(key,"")+" "+old).strip()
    return data


class MalayConservativeRepairTests(unittest.TestCase):
    def setUp(self):
        self.p=synthetic_package()

    def test_exact_twenty_terms_in_seventeen_fields_preserve_original(self):
        initial=deepcopy(self.p)
        self.assertEqual(20,_malay_misconceptions(self.p))
        changed,result=patch_private_semantics(self.p)
        self.assertEqual(0,_malay_misconceptions(changed))
        self.assertEqual(20,result["changedTermOccurrences"])
        self.assertEqual(17,result["changedLocalizedFields"])
        self.assertEqual(initial,self.p)
        self.assertEqual(0,result["formalAcademicPASS"])
        self.assertFalse(result["publicationAuthorized"])
        for pointer,old,new in RULES:
            parent,key=_node(changed,pointer)
            self.assertIn(new,parent[key])
            self.assertNotIn(old,parent[key])

    def test_missing_or_duplicate_original_phrase_rejected(self):
        pointer,old,_=RULES[0]
        parent,key=_node(self.p,pointer)
        parent[key]=parent[key].replace(old,"different")
        with self.assertRaises(ValueError):patch_private_semantics(self.p)
        parent[key]=old+" "+old
        with self.assertRaises(ValueError):patch_private_semantics(self.p)

    def test_unreviewed_extra_mistranslation_rejected(self):
        self.p["activities"][0]["feedback"]={"ms":"daya abadi"}
        with self.assertRaisesRegex(ValueError,"new or missing"):
            patch_private_semantics(self.p)

    def test_versioned_source_verification_and_fail_closed_output(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            pkg=root/"input.json"
            source=root/"source.pdf"
            packets=root/"packets.json"
            out=root/"new-private-v6"
            pkg.write_text(json.dumps(self.p),encoding="utf-8")
            source.write_bytes(b"%PDF-1.4 synthetic")
            packets.write_text(json.dumps({"packageSha256":"old"}))
            original=sha256(pkg.read_bytes()).hexdigest()
            pdf_hash=sha256(source.read_bytes()).hexdigest()
            def verifier(*,package_file,source_pdf,packets_file,expected_count):
                manifest=json.loads(packets_file.read_text())
                raw=package_file.read_bytes()
                if manifest["packageSha256"] != sha256(raw).hexdigest():
                    # The input fixture deliberately starts with wrong manifest:
                    if package_file==pkg:return {
                        "packageSha256":original,"sourceSha256":pdf_hash,
                        "newlyReverifiedSourceActivities":18}
                    raise ValueError("source receipt forged")
                return {
                    "packageSha256":sha256(raw).hexdigest(),
                    "sourceSha256":pdf_hash,
                    "newlyReverifiedSourceActivities":18}
            with patch("app_generator.validation.malay_conservative_semantics.V5_SHA",original),patch(
                "app_generator.validation.malay_conservative_semantics.ORIGINAL_PDF_SHA",pdf_hash
            ),patch(
                "app_generator.validation.malay_conservative_semantics.verify_full_source_packet_roster",
                side_effect=verifier,
            ):
                result=emit_versioned_private_candidate(
                    package_file=pkg,source_pdf=source,packets_file=packets,out_directory=out)
            self.assertEqual(20,result["changedTermOccurrences"])
            self.assertTrue((out/"source-packets-full18.json").exists())
            self.assertEqual(original,sha256(pkg.read_bytes()).hexdigest())
            self.assertFalse(result["publicationAuthorized"])
            with self.assertRaisesRegex(ValueError,"new private version directory"):
                emit_versioned_private_candidate(
                    package_file=pkg,source_pdf=source,packets_file=packets,out_directory=out)


if __name__=="__main__":
    unittest.main()
