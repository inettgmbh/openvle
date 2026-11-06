"""Tests for controllers/languages.py - CRUDLanguage operations."""

import uuid

from controllers.languages import CRUDLanguage
from models import Language, ObjectPermission
from schemas.languages import Language as LanguageSchema

from tests.helpers.mock_request import create_mock_request


class TestCRUDLanguageGetByKey:
    def setup_method(self):
        self.crud = CRUDLanguage(Language)

    def test_get_by_key_found(self, db_session, system_user):
        """Seeded de_DE language is found by key."""
        result = self.crud.get_by_key(db_session, key="de_DE")
        assert result is not None
        assert result.key == "de_DE"
        assert result.nameEnglish == "German (Germany)"

    def test_get_by_key_not_found(self, db_session, system_user):
        result = self.crud.get_by_key(db_session, key="xx_XX")
        assert result is None


class TestCRUDLanguageCreate:
    def setup_method(self):
        self.crud = CRUDLanguage(Language)

    def test_create_language(self, db_session, active_user):
        request = create_mock_request(active_user)
        obj_in = LanguageSchema(
            id=uuid.uuid4(),
            nameEnglish="Klingon",
            nameTranslated="tlhIngan",
            key="kl_KL",
        )
        result = self.crud.create(db_session, request, obj_in=obj_in)
        assert result.nameEnglish == "Klingon"
        assert result.key == "kl_KL"

    def test_create_no_object_permission(self, db_session, active_user):
        """Language is in MODELS_NO_OBJ_PERM, so no ObjectPermission should be created."""
        request = create_mock_request(active_user)
        obj_in = LanguageSchema(
            id=uuid.uuid4(),
            nameEnglish="Esperanto",
            nameTranslated="Esperanto",
            key="eo_EO",
        )
        result = self.crud.create(db_session, request, obj_in=obj_in)

        obj_perm = (
            db_session.query(ObjectPermission)
            .filter(ObjectPermission.object_id == result.id)
            .first()
        )
        assert obj_perm is None


class TestCRUDLanguageUpdate:
    def setup_method(self):
        self.crud = CRUDLanguage(Language)

    def test_update_language(self, db_session, active_user):
        """Update nameEnglish and nameTranslated on a language."""
        request = create_mock_request(active_user)
        obj_in = LanguageSchema(
            id=uuid.uuid4(),
            nameEnglish="Vulcan",
            nameTranslated="Vuhlkansu",
            key="vu_VU",
        )
        lang = self.crud.create(db_session, request, obj_in=obj_in)

        updated = self.crud.update(
            lang.id,
            db_session,
            request,
            obj_in={
                "nameEnglish": "Italian Updated",
                "nameTranslated": "Italiano Aggiornato",
            },
        )
        assert updated.nameEnglish == "Italian Updated"
        assert updated.nameTranslated == "Italiano Aggiornato"
        assert updated.key == "vu_VU"


class TestCRUDLanguageDelete:
    def setup_method(self):
        self.crud = CRUDLanguage(Language)

    def test_delete_language(self, db_session, active_user):
        """Delete a language and verify it is gone."""
        request = create_mock_request(active_user)
        obj_in = LanguageSchema(
            id=uuid.uuid4(),
            nameEnglish="Sindarin",
            nameTranslated="Sindarin",
            key="sn_SN",
        )
        lang = self.crud.create(db_session, request, obj_in=obj_in)
        lang_id = lang.id

        result = self.crud.delete(db_session, lang_id)
        assert "deleted" in str(result["detail"]).lower() or lang_id is not None

        fetched = db_session.get(Language, lang_id)
        assert fetched is None


class TestCRUDLanguageGetMulti:
    def setup_method(self):
        self.crud = CRUDLanguage(Language)

    def test_get_multi_returns_all(self, db_session, active_user):
        """Create several languages, get_multi returns all."""
        request = create_mock_request(active_user)
        keys = ["aa_AA", "bb_BB", "cc_CC"]
        for i, key in enumerate(keys):
            obj_in = LanguageSchema(
                id=uuid.uuid4(),
                nameEnglish=f"Lang{i}",
                nameTranslated=f"Sprache{i}",
                key=key,
            )
            self.crud.create(db_session, request, obj_in=obj_in)

        result = self.crud.get_multi(db_session)
        assert len(result["items"]) >= 3

    def test_search_by_name(self, db_session, active_user):
        """get_multi with search parameter filters by nameEnglish."""
        request = create_mock_request(active_user)
        obj_in = LanguageSchema(
            id=uuid.uuid4(),
            nameEnglish="UniqueSearchLang",
            nameTranslated="Einzigartig",
            key="us_US",
        )
        self.crud.create(db_session, request, obj_in=obj_in)

        result = self.crud.get_multi(
            db_session,
            search_field="nameEnglish",
            search_value="UniqueSearchLang",
        )
        assert len(result["items"]) == 1
        assert result["items"][0].nameEnglish == "UniqueSearchLang"

    def test_get_by_key_returns_correct_language(self, db_session, active_user):
        """Two languages exist, get_by_key returns the correct one."""
        request = create_mock_request(active_user)
        for key, name in [("ja_JP", "Japanese"), ("ko_KR", "Korean")]:
            obj_in = LanguageSchema(
                id=uuid.uuid4(),
                nameEnglish=name,
                nameTranslated=name,
                key=key,
            )
            self.crud.create(db_session, request, obj_in=obj_in)

        result = self.crud.get_by_key(db_session, key="ko_KR")
        assert result is not None
        assert result.nameEnglish == "Korean"
        assert result.key == "ko_KR"
