#!/usr/bin/env python3
"""
RISC-V CPU Test Suite Runner
Runs all test files and provides a comprehensive summary
"""

import unittest
import sys
import os
import subprocess
from io import StringIO
import time

def run_test_file(test_file):
    """Run a single test file and return results"""
    print(f"\n{'='*60}")
    print(f"Running {test_file}...")
    print('='*60)
    
    try:
        # Capture test output
        test_output = StringIO()
        
        # Load and run the test module
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName(test_file.replace('.py', ''))
        runner = unittest.TextTestRunner(stream=test_output, verbosity=2)
        
        start_time = time.time()
        result = runner.run(suite)
        end_time = time.time()
        
        # Print captured output
        output = test_output.getvalue()
        print(output)
        
        execution_time = end_time - start_time
        
        return {
            'file': test_file,
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success': result.wasSuccessful(),
            'time': execution_time
        }
        
    except Exception as e:
        print(f"ERROR: Failed to run {test_file}: {e}")
        return {
            'file': test_file,
            'tests_run': 0,
            'failures': 0,
            'errors': 1,
            'success': False,
            'time': 0,
            'exception': str(e)
        }

def run_integration_test(test_file):
    """Run integration test scripts that aren't unittest modules"""
    print(f"\n{'='*60}")
    print(f"Running {test_file}...")
    print('='*60)
    
    try:
        start_time = time.time()
        
        # Run the script as a subprocess
        result = subprocess.run(
            [sys.executable, test_file], 
            capture_output=True, 
            text=True, 
            timeout=60  # 60 second timeout
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Print the output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"STDERR: {result.stderr}")
        
        success = result.returncode == 0
        
        return {
            'file': test_file,
            'tests_run': 1,  # Integration tests count as 1 test
            'failures': 0 if success else 1,
            'errors': 0,
            'success': success,
            'time': execution_time,
            'return_code': result.returncode
        }
        
    except subprocess.TimeoutExpired:
        print(f"ERROR: {test_file} timed out after 60 seconds")
        return {
            'file': test_file,
            'tests_run': 1,
            'failures': 0,
            'errors': 1,
            'success': False,
            'time': 60,
            'exception': 'Timeout'
        }
    except Exception as e:
        print(f"ERROR: Failed to run {test_file}: {e}")
        return {
            'file': test_file,
            'tests_run': 1,
            'failures': 0,
            'errors': 1,
            'success': False,
            'time': 0,
            'exception': str(e)
        }

def main():
    """Run all CPU tests"""
    print("RISC-V Single-Cycle CPU - Complete Test Suite")
    print("=" * 80)
    
    # List of unittest test files
    unittest_files = [
        'test_register_file.py',
        'test_memory_interface.py', 
        'test_integrated_alu.py',
        'test_instruction_formats.py',
        'test_control_flow.py',
        'test_control_unit.py',
        'test_instruction_decoder.py',
    ]
    
    # List of integration test files (standalone scripts)
    integration_files = [
        'test_datapath.py',
        'test_prog_hex.py',
    ]
    
    # Also check for test files in parent directory
    parent_test_files = []
    parent_dir = os.path.dirname(os.getcwd())
    for test_file in ['test_control_unit.py', 'test_instruction_decoder.py']:
        if os.path.exists(os.path.join(parent_dir, test_file)):
            parent_test_files.append(test_file)
    
    # Filter to only existing files
    existing_unittest_tests = []
    for test_file in unittest_files:
        if os.path.exists(test_file):
            existing_unittest_tests.append(test_file)
        else:
            print(f"WARNING: {test_file} not found, skipping...")
    
    existing_integration_tests = []
    for test_file in integration_files:
        if os.path.exists(test_file):
            existing_integration_tests.append(test_file)
        else:
            print(f"WARNING: {test_file} not found, skipping...")
    
    total_test_files = len(existing_unittest_tests) + len(existing_integration_tests) + len(parent_test_files)
    
    if total_test_files == 0:
        print("ERROR: No test files found!")
        return False
    
    print(f"Found {len(existing_unittest_tests)} unittest files, {len(existing_integration_tests)} integration tests...")
    
    # Run all tests
    results = []
    total_start_time = time.time()
    
    # Run unittest files
    for test_file in existing_unittest_tests:
        result = run_test_file(test_file)
        results.append(result)
    
    # Run integration test files
    for test_file in existing_integration_tests:
        result = run_integration_test(test_file)
        results.append(result)
    
    # Run parent directory tests if they exist
    if parent_test_files:
        print(f"\n{'='*60}")
        print("Running tests from parent directory...")
        print('='*60)
        
        original_dir = os.getcwd()
        try:
            os.chdir(parent_dir)
            for test_file in parent_test_files:
                result = run_test_file(test_file)
                results.append(result)
        finally:
            os.chdir(original_dir)
    
    total_end_time = time.time()
    total_time = total_end_time - total_start_time
    
    # Print comprehensive summary
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print('='*80)
    
    total_tests = 0
    total_failures = 0
    total_errors = 0
    successful_files = 0
    
    for result in results:
        status = "PASS" if result['success'] else "FAIL"
        time_str = f"{result['time']:.2f}s"
        
        print(f"{status} {result['file']:<25} | "
              f"Tests: {result['tests_run']:<3} | "
              f"Failures: {result['failures']:<2} | "
              f"Errors: {result['errors']:<2} | "
              f"Time: {time_str}")
        
        if 'exception' in result:
            print(f"      Exception: {result['exception']}")
        elif 'return_code' in result and result['return_code'] != 0:
            print(f"      Exit code: {result['return_code']}")
        
        total_tests += result['tests_run']
        total_failures += result['failures']
        total_errors += result['errors']
        
        if result['success']:
            successful_files += 1
    
    print('-' * 80)
    print(f"TOTALS:")
    print(f"  Files run: {len(results)} | Successful: {successful_files} | Failed: {len(results) - successful_files}")
    print(f"  Tests run: {total_tests} | Failures: {total_failures} | Errors: {total_errors}")
    print(f"  Total time: {total_time:.2f} seconds")
    
    # Overall result
    all_passed = total_failures == 0 and total_errors == 0
    
    if all_passed:
        print(f"\nAll Tests Passed! RISC-V CPU implementation is working correctly")
    else:
        print(f"\nSome tests failed. Check the output above for details.")
    
    print('='*80)
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)