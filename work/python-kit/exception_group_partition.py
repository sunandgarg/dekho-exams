def leaf_types(failure):
    if isinstance(failure, BaseExceptionGroup):
        return [name for child in failure.exceptions for name in leaf_types(child)]
    return [type(failure).__name__]

batch = ExceptionGroup("import", [ValueError("amount"),
    ExceptionGroup("row", [OSError("read"), ValueError("identifier")])])
matched, residual = batch.split(ValueError)
print("matched:", leaf_types(matched))
print("residual:", leaf_types(residual))
print("original:", leaf_types(batch))
print("nested remainder:", isinstance(residual.exceptions[0], ExceptionGroup))
