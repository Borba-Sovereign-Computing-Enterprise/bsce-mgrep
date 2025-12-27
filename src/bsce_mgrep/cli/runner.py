"""Orchestrate pipeline execution.

This module wires together all components and executes the mgrep pipeline.
Uses dependency injection via the hexagonal architecture.
"""

import sys
from result import Result, Ok, Err

from bsce_mgrep.cli.parser import CLIArgs, _is_stdin_piped
from bsce_mgrep.adapters.input.file_reader import FileReader
from bsce_mgrep.adapters.input.stdin_reader import StdinReader
from bsce_mgrep.adapters.output.line_emitter import LineEmitter
from bsce_mgrep.domain.matcher import create_matcher, MatchConfig
from bsce_mgrep.domain.filter import create_filter
from bsce_mgrep.domain.pipeline import build_pipeline
from bsce_mgrep.ports.reader import SourceReader

def run(args: CLIArgs) -> Result[None, str]:
    """Execute the mgrep pipeline.
    
    Orchestration steps:
    1. Select appropriate reader (file or stdin)
    2. Create matcher from pattern
    3. Create filter from where clauses
    4. Build and execute pipeline
    5. Emit results to stdout
    
    Args:
        args: Parsed CLI arguments
        
    Returns:
        Ok(None) on success, Err(message) on failure
        
    Examples:
        >>> from bsce_mgrep.cli.parser import CLIArgs
        >>> args = CLIArgs(
        ...     source="test.log",
        ...     pattern="ERROR",
        ...     case_sensitive=False,
        ...     where_clauses=[]
        ... )
        >>> # run(args)  # Would execute the pipeline
    """
    # Step 1: Select reader based on source
    reader_result = _select_reader(args.source)
    
    match reader_result:
        case Err(error):
            return Err(error)
        case Ok(reader):
            pass
    
    # Step 2: Create matcher
    matcher = create_matcher(MatchConfig(
        pattern=args.pattern,
        case_sensitive=args.case_sensitive
    ))
    
    # Step 3: Create filter
    filter_fn = create_filter(args.where_clauses)
    
    # Step 4: Build pipeline
    pipeline = build_pipeline(matcher, filter_fn)
    
    # Step 5: Execute pipeline
    try:
        lines = reader.read_lines()
        contexts = pipeline(lines)
        
        # Step 6: Emit results
        emitter = LineEmitter(show_line_numbers=False)
        emitter.emit(contexts)
        
        return Ok(None)
    
    except BrokenPipeError:
        # Normal when piping to head, etc.
        # Python writes to stdout, but the reader closed the pipe
        # This is not an error - just cleanup and exit
        devnull = open('/dev/null', 'w')
        sys.stdout = devnull
        return Ok(None)
    
    except KeyboardInterrupt:
        # User interrupted with Ctrl+C
        return Err("Interrupted by user")
    
    except Exception as e:
        # Unexpected error
        return Err(f"Unexpected error: {e}")

def _select_reader(source: str | None) -> Result[SourceReader, str]:
    """Select appropriate reader based on source.
    
    Logic:
    - If source is None and stdin is piped → StdinReader
    - If source is None and stdin is not piped → Error
    - If source is a filepath → FileReader
    
    Args:
        source: File path or None
        
    Returns:
        Result containing a SourceReader or error message
        
    Examples:
        >>> result = _select_reader("test.log")
        >>> isinstance(result.ok_value, FileReader)
        True
    """
    match source:
        case None if _is_stdin_piped():
            return Ok(StdinReader())
        
        case None:
            return Err("No input source: provide a file path or pipe input via stdin")
        
        case str(filepath) if filepath.strip():
            return Ok(FileReader(filepath=filepath))
        
        case _:
            return Err(f"Invalid source: {source}")

def run_with_stats(args: CLIArgs) -> Result[tuple[int, int], str]:
    """Execute pipeline and return statistics.
    
    Like run(), but returns match and error counts instead of emitting.
    Useful for testing and batch processing.
    
    Args:
        args: Parsed CLI arguments
        
    Returns:
        Ok((match_count, error_count)) or Err(message)
        
    Examples:
        >>> from bsce_mgrep.cli.parser import CLIArgs
        >>> args = CLIArgs(
        ...     source="test.log",
        ...     pattern="ERROR",
        ...     case_sensitive=False,
        ...     where_clauses=[]
        ... )
        >>> # result = run_with_stats(args)
        >>> # match_count, error_count = result.ok_value
    """
    reader_result = _select_reader(args.source)
    
    match reader_result:
        case Err(error):
            return Err(error)
        case Ok(reader):
            pass
    
    matcher = create_matcher(MatchConfig(
        pattern=args.pattern,
        case_sensitive=args.case_sensitive
    ))
    
    filter_fn = create_filter(args.where_clauses)
    pipeline = build_pipeline(matcher, filter_fn)
    
    try:
        lines = reader.read_lines()
        contexts = pipeline(lines)
        
        # Count instead of emit
        match_count = 0
        error_count = 0
        
        for result in contexts:
            match result:
                case Ok(_):
                    match_count += 1
                case Err(_):
                    error_count += 1
        
        return Ok((match_count, error_count))
    
    except Exception as e:
        return Err(f"Unexpected error: {e}")
