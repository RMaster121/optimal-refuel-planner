"""Tests for Country model."""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from fuel_prices.models import Country


@pytest.mark.integration
class TestCountryModel:
    """Tests for Country model."""

    def test_create_country_with_valid_data(self, db):
        """Should create country with valid ISO code and name."""
        country = Country.objects.create(
            code='PL',
            name='Poland'
        )
        
        assert country.code == 'PL'
        assert country.name == 'Poland'

    def test_create_country_normalizes_code_to_uppercase(self, db):
        """Should normalize country code to uppercase in clean()."""
        country = Country(code='pl', name='Poland')
        country.full_clean()
        country.save()
        
        assert country.code == 'PL'

    def test_str_representation(self, db):
        """Should return formatted string with name and code."""
        country = Country.objects.create(
            code='DE',
            name='Germany'
        )
        
        assert str(country) == 'Germany (DE)'

    def test_str_with_lowercase_code_displays_uppercase(self, db):
        """Should display code as uppercase in string representation."""
        country = Country(code='fr', name='France')
        country.full_clean()
        country.save()
        
        # Code stored as uppercase after normalization
        assert str(country) == 'France (FR)'

    def test_code_is_required(self, db):
        """Should raise ValidationError when code is missing."""
        country = Country(name='Poland')
        
        with pytest.raises(ValidationError) as exc_info:
            country.full_clean()
        
        assert 'code' in exc_info.value.error_dict

    def test_name_is_required(self, db):
        """Should raise ValidationError when name is missing."""
        country = Country(code='PL')
        
        with pytest.raises(ValidationError) as exc_info:
            country.full_clean()
        
        assert 'name' in exc_info.value.error_dict

    def test_name_cannot_be_blank(self, db):
        """Should raise ValidationError for blank name."""
        country = Country(code='PL', name='')
        
        with pytest.raises(ValidationError) as exc_info:
            country.full_clean()
        
        assert 'name' in exc_info.value.error_dict
        assert 'cannot be blank' in str(exc_info.value.error_dict['name'])

    def test_name_cannot_be_whitespace_only(self, db):
        """Should raise ValidationError for whitespace-only name."""
        country = Country(code='PL', name='   ')
        
        with pytest.raises(ValidationError) as exc_info:
            country.full_clean()
        
        assert 'name' in exc_info.value.error_dict

    def test_code_must_be_exactly_two_letters(self, db):
        """Should raise ValidationError for code not exactly 2 letters."""
        # Too short
        country = Country(code='P', name='Poland')
        with pytest.raises(ValidationError) as exc_info:
            country.full_clean()
        assert 'code' in exc_info.value.error_dict

        # Too long
        country = Country(code='POL', name='Poland')
        with pytest.raises(ValidationError) as exc_info:
            country.full_clean()
        assert 'code' in exc_info.value.error_dict

    def test_code_must_be_letters_only(self, db):
        """Should raise ValidationError for non-letter characters in code."""
        country = Country(code='P1', name='Poland')
        
        with pytest.raises(ValidationError) as exc_info:
            country.full_clean()
        
        assert 'code' in exc_info.value.error_dict

    def test_code_must_be_uppercase_or_normalizable(self, db):
        """Should accept lowercase code and normalize it."""
        country = Country(code='de', name='Germany')
        country.full_clean()
        
        assert country.code == 'DE'

    def test_code_is_unique(self, db):
        """Should enforce unique constraint on code."""
        Country.objects.create(code='PL', name='Poland')
        
        with pytest.raises(ValidationError):
            Country.objects.create(code='PL', name='Polska')

    def test_name_is_unique(self, db):
        """Should enforce unique constraint on name."""
        Country.objects.create(code='PL', name='Poland')
        
        with pytest.raises(ValidationError):
            Country.objects.create(code='PO', name='Poland')

    def test_ordering_by_name(self, db):
        """Should order countries by name."""
        Country.objects.create(code='DE', name='Germany')
        Country.objects.create(code='PL', name='Poland')
        Country.objects.create(code='FR', name='France')
        
        countries = list(Country.objects.all())
        
        assert countries[0].name == 'France'
        assert countries[1].name == 'Germany'
        assert countries[2].name == 'Poland'

    def test_validated_model_calls_full_clean_on_save(self, db):
        """Should call full_clean() on save (ValidatedModel behavior)."""
        country = Country(code='invalid', name='Test')
        
        with pytest.raises(ValidationError):
            country.save()

    def test_country_fixture_poland(self, country_poland):
        """Should work with country_poland fixture."""
        assert country_poland.code == 'PL'
        assert country_poland.name == 'Poland'
        assert str(country_poland) == 'Poland (PL)'

    def test_country_fixture_germany(self, country_germany):
        """Should work with country_germany fixture."""
        assert country_germany.code == 'DE'
        assert country_germany.name == 'Germany'
        assert str(country_germany) == 'Germany (DE)'

    def test_multiple_countries_can_coexist(self, db):
        """Should allow multiple different countries."""
        pl = Country.objects.create(code='PL', name='Poland')
        de = Country.objects.create(code='DE', name='Germany')
        fr = Country.objects.create(code='FR', name='France')
        
        assert Country.objects.count() == 3
        assert pl.code == 'PL'
        assert de.code == 'DE'
        assert fr.code == 'FR'

    def test_clean_strips_whitespace_from_code(self, db):
        """Should strip whitespace from code during clean."""
        country = Country(code='  PL  ', name='Poland')
        country.full_clean()
        
        assert country.code == 'PL'

    def test_code_normalization_happens_in_clean(self, db):
        """Should normalize code in clean() before validators run."""
        country = Country(code='pl', name='Poland')
        country.clean_fields()  # This should normalize the code
        
        assert country.code == 'PL'
        
        country.full_clean()
        country.save()
        
        assert country.code == 'PL'