import os
import sys
import pytest
from pathlib import Path # Use pathlib for easier path manipulation

# Add src directory to sys.path to allow importing peersight module
# This assumes tests are run from the project root directory
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Now import the module to be tested
from peersight import utils
from peersight import config # Needed for default encoding

# --- Test Fixtures ---
@pytest.fixture(scope="function") # Rerun fixture for each test function
def temp_test_dir(tmp_path):
    """Creates a temporary directory for test files."""
    # tmp_path is a pytest fixture providing a Path object to a temporary directory
    test_dir = tmp_path / "test_files"
    test_dir.mkdir()
    print(f"Created temp test dir: {test_dir}") # Debug print
    return test_dir

# --- Tests for read_text_file ---

def test_read_text_file_success(temp_test_dir):
    """Test reading a simple text file successfully."""
    file_path = temp_test_dir / "test_read.txt"
    expected_content = "This is a test file.\nWith multiple lines."
    # Use utf-8 explicitly for writing test file
    with open(file_path, "w", encoding=config.DEFAULT_ENCODING) as f:
        f.write(expected_content)

    content = utils.read_text_file(str(file_path)) # Convert Path to string for function
    assert content is not None
    assert content == expected_content

def test_read_text_file_not_found(temp_test_dir):
    """Test reading a non-existent file."""
    file_path = temp_test_dir / "non_existent.txt"
    content = utils.read_text_file(str(file_path))
    assert content is None

def test_read_text_file_different_encoding_success(temp_test_dir):
    """Test reading a file with a non-default encoding (if specified)."""
    file_path = temp_test_dir / "test_encoding.txt"
    expected_content = "Test content with accents: éàçü"
    test_encoding = "latin-1" # Example different encoding
    # Write with the specific encoding
    with open(file_path, "w", encoding=test_encoding) as f:
        f.write(expected_content)

    # Read specifying the correct encoding
    content = utils.read_text_file(str(file_path), encoding=test_encoding)
    assert content is not None
    assert content == expected_content

def test_read_text_file_wrong_encoding_fails(temp_test_dir):
    """Test reading a file with the wrong encoding specified fails."""
    file_path = temp_test_dir / "test_wrong_encoding.txt"
    # Content with characters not typically in default encoding
    content_to_write = "你好世界" # Example Chinese characters likely failing default decode
    write_encoding = "utf-8"
    read_encoding = "ascii" # Intentionally wrong encoding

    with open(file_path, "w", encoding=write_encoding) as f:
        f.write(content_to_write)

    # Expect None due to UnicodeDecodeError (or potentially different error)
    content = utils.read_text_file(str(file_path), encoding=read_encoding)
    assert content is None # The function should catch the decode error and return None


# --- Tests for write_text_file ---

def test_write_text_file_success(temp_test_dir):
    """Test writing a simple text file successfully."""
    file_path = temp_test_dir / "test_write.txt"
    content_to_write = "Content to be written.\nLine 2."

    success = utils.write_text_file(str(file_path), content_to_write)
    assert success is True

    # Verify the content was written correctly
    assert file_path.exists()
    with open(file_path, "r", encoding=config.DEFAULT_ENCODING) as f:
        read_content = f.read()
    assert read_content == content_to_write

def test_write_text_file_creates_directory(temp_test_dir):
    """Test that write_text_file creates parent directories."""
    nested_dir = temp_test_dir / "nested" / "dir"
    file_path = nested_dir / "test_nested_write.txt"
    content_to_write = "Testing nested directory creation."

    # Ensure directory does NOT exist initially
    assert not nested_dir.exists()

    success = utils.write_text_file(str(file_path), content_to_write)
    assert success is True

    # Verify directory and file exist and content is correct
    assert nested_dir.exists()
    assert file_path.exists()
    with open(file_path, "r", encoding=config.DEFAULT_ENCODING) as f:
        read_content = f.read()
    assert read_content == content_to_write

# Note: Testing write failures (e.g., due to permissions) is harder
# in a standard unit test setup and often skipped or done differently.