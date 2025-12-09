"""Custom test runner with colorized output and better formatting."""

import sys
import time
import unittest
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from unittest.runner import _WritelnDecorator

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BOLD = '\033[1m'
RESET = '\033[0m'


class ColorTextTestResult(unittest.TextTestResult):
    """Custom test result class with colorized output and output buffering."""

    def __init__(self, stream: "_WritelnDecorator", descriptions: bool, verbosity: int) -> None:
        super().__init__(stream, descriptions, verbosity)
        self.buffer = True  # Enable output buffering
        self.current_class = None
        self.start_time = None

    def startTest(self, test):
        """Called when a test starts."""
        super().startTest(test)

        # Track test class changes for grouping
        test_class = test.__class__.__name__
        if test_class != self.current_class:
            self.current_class = test_class
            self.stream.write('\n')
            self.stream.write('═' * 43)
            self.stream.write('\n')
            self.stream.write(f'{BOLD}{test_class}{RESET}\n')
            self.stream.write('─' * 43)
            self.stream.write('\n')
            self.stream.flush()

    def addSuccess(self, test):
        """Called when a test passes."""
        super().addSuccess(test)
        if self.showAll:
            test_method = test._testMethodName
            self.stream.write(f'{GREEN}✓{RESET} {test_method}\n')
            self.stream.flush()
        elif self.dots:
            self.stream.write(f'{GREEN}.{RESET}')
            self.stream.flush()

    def addError(self, test, err):
        """Called when a test has an error."""
        super().addError(test, err)
        if self.showAll:
            test_method = test._testMethodName
            self.stream.write(f'{RED}{BOLD}E{RESET} {test_method}\n')
            self.stream.flush()
        elif self.dots:
            self.stream.write(f'{RED}{BOLD}E{RESET}')
            self.stream.flush()

    def addFailure(self, test, err):
        """Called when a test fails."""
        super().addFailure(test, err)
        if self.showAll:
            test_method = test._testMethodName
            self.stream.write(f'{RED}F{RESET} {test_method}\n')
            self.stream.flush()
        elif self.dots:
            self.stream.write(f'{RED}F{RESET}')
            self.stream.flush()

    def addSkip(self, test, reason):
        """Called when a test is skipped."""
        super().addSkip(test, reason)
        if self.showAll:
            test_method = test._testMethodName
            self.stream.write(f'{YELLOW}s{RESET} {test_method} (skipped: {reason})\n')
            self.stream.flush()
        elif self.dots:
            self.stream.write(f'{YELLOW}s{RESET}')
            self.stream.flush()

    def printErrors(self):
        """Print errors and failures with captured output."""
        if self.dots or self.showAll:
            self.stream.write('\n')
        self.printErrorList('ERROR', self.errors)
        self.printErrorList('FAIL', self.failures)

    def printErrorList(self, flavour, errors):
        """Print formatted error list with captured output."""
        for test, err in errors:
            self.stream.write('\n')
            self.stream.write('═' * 43)
            self.stream.write('\n')
            self.stream.write(f'{RED}{BOLD}{flavour}: {self.getDescription(test)}{RESET}\n')
            self.stream.write('─' * 43)
            self.stream.write('\n')
            self.stream.write(f'{err}\n')


class ColorTestRunner(unittest.TextTestRunner):
    """Custom test runner that uses ColorTextTestResult."""

    resultclass = ColorTextTestResult  # type: ignore[assignment]

    def __init__(self, stream=None, descriptions=True, verbosity=2,
                 failfast=False, buffer=True, resultclass=None, warnings=None,
                 *, tb_locals=False):
        super().__init__(
            stream=stream,
            descriptions=descriptions,
            verbosity=verbosity,
            failfast=failfast,
            buffer=buffer,
            resultclass=resultclass or ColorTextTestResult,  # type: ignore[arg-type]
            warnings=warnings,
            tb_locals=tb_locals
        )

    def run(self, test):
        """Run tests with timing and colorized summary."""
        start_time = time.time()
        result = super().run(test)
        elapsed = time.time() - start_time

        # Print summary
        self.stream.write('\n')
        self.stream.write('═' * 43)
        self.stream.write('\n')

        # Determine summary color and message
        if result.wasSuccessful():
            color = GREEN
            msg = f'{result.testsRun} tests passed in {elapsed:.2f}s'
        else:
            color = RED
            passed = result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)
            failed = len(result.failures) + len(result.errors)
            parts = [f'{passed} passed', f'{failed} failed']
            if result.skipped:
                parts.append(f'{len(result.skipped)} skipped')
            msg = f'{", ".join(parts)} in {elapsed:.2f}s'

        self.stream.write(f'{color}{msg}{RESET}\n')
        self.stream.write('═' * 43)
        self.stream.write('\n')

        return result


def run_tests():
    """Discover and run all tests with colorized output."""
    loader = unittest.TestLoader()
    start_dir = 'tests'
    suite = loader.discover(start_dir, pattern='test_*.py')

    runner = ColorTestRunner(verbosity=2)
    result = runner.run(suite)

    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
